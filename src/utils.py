from __future__ import annotations

import re
from typing import Iterable

_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_URL_RE = re.compile(r"\bhttps?://[^\s)\]]+", re.IGNORECASE)

_WHITESPACE_RE = re.compile(r"\s+")
_BULLET_RE = re.compile(r"^\s*([\-\*•]|\d+\.|\d+\))\s+")


def normalize_space(text: str) -> str:
    return _WHITESPACE_RE.sub(" ", text or "").strip()


def multiline_to_list(raw: str) -> list[str]:
    if not raw:
        return []
    items: list[str] = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        line = _BULLET_RE.sub("", line).strip()
        if line:
            items.append(line)
    # de-dup preserving order
    seen = set()
    out: list[str] = []
    for it in items:
        key = it.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(it)
    return out


def list_to_multiline(items: Iterable[str] | None) -> str:
    if not items:
        return ""
    return "\n".join(str(x).strip() for x in items if str(x).strip())


def extract_emails(text: str) -> list[str]:
    if not text:
        return []
    return sorted(set(_EMAIL_RE.findall(text)))


def extract_urls(text: str) -> list[str]:
    if not text:
        return []
    return sorted(set(_URL_RE.findall(text)))


def looks_like_url(url: str) -> bool:
    if not url:
        return False
    url = url.strip()
    return bool(re.match(r"^https?://", url, re.IGNORECASE))


def clamp_str(text: str, max_chars: int) -> str:
    if text is None:
        return ""
    text = str(text)
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1] + "…"
