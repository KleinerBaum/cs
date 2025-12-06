# src/wizard/streamlit_renderer.py
from __future__ import annotations

from typing import Any

import streamlit as st

from cogstaff.schema.profile_document import (
    FieldSource,
    NeedAnalysisProfileDocument,
    get_value_by_path,
    update_field,
)
from cogstaff.wizard.question_engine import QuestionSpec, StepPlan


def _lang(doc: NeedAnalysisProfileDocument) -> str:
    return getattr(doc.ui_language, "value", str(doc.ui_language))


def _label(doc: NeedAnalysisProfileDocument, q: QuestionSpec) -> str:
    return q.label.get(_lang(doc))


def _help(doc: NeedAnalysisProfileDocument, q: QuestionSpec) -> str | None:
    return q.help.get(_lang(doc)) if q.help else None


def _enum_to_str(v: Any) -> Any:
    return getattr(v, "value", v)


def _parse_list_text(raw: str) -> list[str]:
    items = []
    for line in (raw or "").splitlines():
        s = line.strip().lstrip("-•").strip()
        if s:
            items.append(s)
    # de-dupe stable
    seen = set()
    out = []
    for x in items:
        k = x.casefold()
        if k not in seen:
            seen.add(k)
            out.append(x)
    return out


def render_question(
    doc: NeedAnalysisProfileDocument, q: QuestionSpec, *, key_prefix: str
) -> None:
    path = q.paths[
        0
    ]  # renderer expects 1 path per widget; multi-path can be handled by custom widget later
    current = get_value_by_path(doc.profile, path)
    current = _enum_to_str(current)

    prov = doc.provenance.get(path)
    warn = (
        prov is not None
        and prov.source != FieldSource.USER
        and (prov.confidence is None or prov.confidence < q.min_confidence)
    )

    label = _label(doc, q)
    if warn:
        label = f"⚠️ {label}"

    help_text = _help(doc, q)
    widget_key = f"{key_prefix}.{q.id}"

    if q.widget == "text":
        val = st.text_input(
            label,
            value="" if current is None else str(current),
            help=help_text,
            key=widget_key,
        )
        if val != ("" if current is None else str(current)):
            update_field(doc, path, val, source=FieldSource.USER, confidence=1.0)

    elif q.widget == "textarea":
        val = st.text_area(
            label,
            value="" if current is None else str(current),
            help=help_text,
            key=widget_key,
            height=120,
        )
        if val != ("" if current is None else str(current)):
            update_field(doc, path, val, source=FieldSource.USER, confidence=1.0)

    elif q.widget == "number":
        # allow empty -> None using text_input fallback if current is None
        if current is None:
            raw = st.text_input(label, value="", help=help_text, key=widget_key)
            if raw.strip():
                try:
                    num = float(raw) if "." in raw else int(raw)
                    update_field(
                        doc, path, num, source=FieldSource.USER, confidence=1.0
                    )
                except ValueError:
                    st.error("Bitte eine Zahl eingeben.")
        else:
            # streamlit number_input needs a number; keep it simple
            val = st.number_input(
                label, value=float(current), help=help_text, key=widget_key
            )
            if float(val) != float(current):
                update_field(
                    doc, path, float(val), source=FieldSource.USER, confidence=1.0
                )

    elif q.widget == "select":
        opts = list(q.options or ())
        if current is not None and str(current) not in [str(o) for o in opts]:
            opts = [current] + opts
        index = 0
        if current is not None:
            for i, o in enumerate(opts):
                if str(o) == str(current):
                    index = i
                    break
        val = st.selectbox(
            label, options=opts, index=index, help=help_text, key=widget_key
        )
        val = _enum_to_str(val)
        if str(val) != ("" if current is None else str(current)):
            update_field(doc, path, val, source=FieldSource.USER, confidence=1.0)

    elif q.widget == "tri_bool":
        # True/False/Unknown
        mapping = {"unknown": None, "yes": True, "no": False}
        inv = {None: "unknown", True: "yes", False: "no"}
        cur_key = inv.get(current if isinstance(current, bool) else None, "unknown")
        opts = ["unknown", "yes", "no"]
        val = st.selectbox(
            label,
            options=opts,
            index=opts.index(cur_key),
            help=help_text,
            key=widget_key,
        )
        decoded = mapping[val]
        if decoded != current:
            update_field(doc, path, decoded, source=FieldSource.USER, confidence=1.0)

    elif q.widget == "list_text":
        existing = current if isinstance(current, list) else []
        raw_default = "\n".join(str(x) for x in existing)
        raw = st.text_area(
            label, value=raw_default, help=help_text, key=widget_key, height=160
        )
        parsed = _parse_list_text(raw)
        if parsed != existing:
            update_field(doc, path, parsed, source=FieldSource.USER, confidence=1.0)

    else:
        st.warning(f"Unbekannter Widget-Typ: {q.widget}")


def render_step(
    doc: NeedAnalysisProfileDocument, plan: StepPlan, *, max_primary_hint: int = 8
) -> None:
    st.caption(
        f"Pflicht offen: {plan.required_remaining}/{plan.required_total} — "
        f"Optional offen: {plan.optional_remaining} — "
        f"Primary zeigt max. ~{max_primary_hint}"
    )

    # one-click confirm for low-confidence/extracted suggestions shown on screen
    if st.button("✅ Sichtbare Vorschläge bestätigen (ohne Änderungen)"):
        st.session_state["_confirm_clicked"] = True  # optional flag for debugging
        # the engine method is called outside, because it needs the engine instance there

    for pq in plan.primary:
        render_question(doc, pq.spec, key_prefix=f"step.{plan.step.value}.primary")

    if plan.detail:
        with st.expander("Mehr Details"):
            for pq in plan.detail:
                render_question(
                    doc, pq.spec, key_prefix=f"step.{plan.step.value}.detail"
                )
