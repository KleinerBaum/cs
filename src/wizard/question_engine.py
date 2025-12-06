# src/wizard/question_engine.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Optional

from cogstaff.schema.profile_document import (
    FieldSource,
    NeedAnalysisProfileDocument,
    get_value_by_path,
)
from cogstaff.wizard.steps import StepId


# ---------- i18n primitive ----------

@dataclass(frozen=True)
class I18nText:
    de: str
    en: str

    def get(self, lang: str) -> str:
        return self.de if lang == "de" else self.en


# ---------- helper: missing / confirm logic ----------

def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, bool):
        return False
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, dict, tuple, set)):
        return len(value) == 0
    return False


@dataclass(frozen=True)
class NeedEval:
    needed: bool
    reason: str  # "missing" | "confirm" | "ok"
    missing_paths: tuple[str, ...] = ()
    confirm_paths: tuple[str, ...] = ()


def evaluate_paths(
    doc: NeedAnalysisProfileDocument,
    paths: Iterable[str],
    *,
    min_confidence: float,
    always_confirm_ai_suggestions: bool = True,
) -> NeedEval:
    missing: list[str] = []
    confirm: list[str] = []

    for path in paths:
        value = get_value_by_path(doc.profile, path)
        if _is_missing(value):
            missing.append(path)
            continue

        prov = doc.provenance.get(path)
        if prov is None:
            confirm.append(path)
            continue

        if prov.source == FieldSource.USER:
            continue

        if always_confirm_ai_suggestions and prov.source == FieldSource.AI_SUGGESTION:
            # AI suggestions should be acknowledged/confirmed explicitly (or via "confirm all")
            confirm.append(path)
            continue

        if prov.confidence is not None and prov.confidence < min_confidence:
            confirm.append(path)

    if missing:
        return NeedEval(True, "missing", tuple(missing), tuple(confirm))
    if confirm:
        return NeedEval(True, "confirm", tuple(missing), tuple(confirm))
    return NeedEval(False, "ok")


# ---------- question spec ----------

Predicate = Callable[[NeedAnalysisProfileDocument], bool]
AskOverride = Callable[[NeedAnalysisProfileDocument], NeedEval]


def _always(_: NeedAnalysisProfileDocument) -> bool:
    return True


@dataclass(frozen=True)
class QuestionSpec:
    """
    A single question = 1 widget (usually) mapped to one or more profile paths.
    """
    id: str
    step: StepId
    paths: tuple[str, ...]
    label: I18nText
    help: Optional[I18nText] = None

    # Streamlit widget type your renderer will map
    widget: str = "text"  # text|textarea|select|multiselect|number|checkbox|tri_bool|list_text

    # ranking / visibility
    required: bool = False
    level: str = "core"  # core|standard|detail
    show_if: Predicate = _always

    # evaluation
    min_confidence: float = 0.65
    ask_override: Optional[AskOverride] = None

    # for select / multiselect
    options: Optional[tuple[Any, ...]] = None

    def evaluate(self, doc: NeedAnalysisProfileDocument) -> NeedEval:
        if not self.show_if(doc):
            return NeedEval(False, "ok")
        if self.ask_override:
            return self.ask_override(doc)
        return evaluate_paths(doc, self.paths, min_confidence=self.min_confidence)


@dataclass(frozen=True)
class PlannedQuestion:
    spec: QuestionSpec
    eval: NeedEval
    score: int


@dataclass(frozen=True)
class StepPlan:
    step: StepId
    primary: tuple[PlannedQuestion, ...]
    detail: tuple[PlannedQuestion, ...]
    required_total: int
    required_remaining: int
    optional_remaining: int


class QuestionEngine:
    def __init__(self, catalog: list[QuestionSpec]):
        self._catalog = catalog

    @property
    def catalog(self) -> list[QuestionSpec]:
        return self._catalog

    def completeness(self, doc: NeedAnalysisProfileDocument) -> dict[StepId, StepPlan]:
        """
        Computes remaining questions for every step based on *full* catalog.
        (primary/detail splitting is still applied, but counts are global per step)
        """
        result: dict[StepId, StepPlan] = {}
        for step in StepId:
            result[step] = self.plan_step(doc, step, max_primary=10, include_detail=True)
        return result

    def plan_step(
        self,
        doc: NeedAnalysisProfileDocument,
        step: StepId,
        *,
        max_primary: int = 8,
        include_detail: bool = False,
        extra_questions: Iterable[QuestionSpec] = (),
    ) -> StepPlan:
        candidates = [q for q in (self._catalog + list(extra_questions)) if q.step == step and q.show_if(doc)]

        planned: list[PlannedQuestion] = []
        required_total = sum(1 for q in candidates if q.required)

        required_remaining = 0
        optional_remaining = 0

        for q in candidates:
            ev = q.evaluate(doc)
            if not ev.needed:
                continue

            base = 100 if q.required else 30
            # missing should outrank confirm
            score = base + 50 * len(ev.missing_paths) + 15 * len(ev.confirm_paths)

            # keep details out of primary by default
            if q.level == "detail":
                score -= 25
            elif q.level == "standard":
                score -= 5

            planned.append(PlannedQuestion(q, ev, score))

            if q.required:
                required_remaining += 1
            else:
                optional_remaining += 1

        planned.sort(key=lambda x: x.score, reverse=True)

        primary_pool = [pq for pq in planned if pq.spec.level in ("core", "standard")]
        detail_pool = [pq for pq in planned if pq.spec.level == "detail"]

        primary = tuple(primary_pool[:max_primary])
        detail = tuple(detail_pool if include_detail else ())

        return StepPlan(
            step=step,
            primary=primary,
            detail=detail,
            required_total=required_total,
            required_remaining=required_remaining,
            optional_remaining=optional_remaining,
        )

    def critical_paths_for_llm(self, doc: NeedAnalysisProfileDocument, step: StepId) -> list[str]:
        """
        Feed this into optional LLM-followups: only required + still missing/confirm.
        """
        plan = self.plan_step(doc, step, max_primary=50, include_detail=True)
        out: list[str] = []
        for pq in (*plan.primary, *plan.detail):
            if not pq.spec.required:
                continue
            out.extend(pq.eval.missing_paths)
            out.extend(pq.eval.confirm_paths)
        # unique but stable-ish
        seen: set[str] = set()
        deduped: list[str] = []
        for p in out:
            if p not in seen:
                seen.add(p)
                deduped.append(p)
        return deduped

    def confirm_visible(
        self,
        doc: NeedAnalysisProfileDocument,
        plan: StepPlan,
        *,
        note: str = "confirmed_in_step",
    ) -> int:
        """
        Mark all visible (primary+detail) confirm-paths as USER with confidence=1.0
        without changing the values.
        Returns count affected paths.
        """
        from cogstaff.schema.profile_document import FieldProvenance  # local to avoid cycles

        touched = 0
        for pq in (*plan.primary, *plan.detail):
            for path in pq.eval.confirm_paths:
                value = get_value_by_path(doc.profile, path)
                if _is_missing(value):
                    continue
                doc.provenance[path] = FieldProvenance(
                    source=FieldSource.USER,
                    confidence=1.0,
                    extractor=None,
                    evidence=[],
                    notes=note,
                )
                touched += 1
        return touched
