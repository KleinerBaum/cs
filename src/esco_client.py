from __future__ import annotations

import urllib.parse
from typing import Any

import requests

from .settings import ESCO_BASE_URL, REQUEST_TIMEOUT_S, USER_AGENT


class ESCOError(RuntimeError):
    pass


def _headers(language: str | None) -> dict[str, str]:
    h = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if language:
        h["Accept-Language"] = language
    return h


def _get(
    url: str, params: dict[str, Any] | None = None, language: str | None = None
) -> dict[str, Any]:
    try:
        resp = requests.get(
            url,
            params=params or {},
            headers=_headers(language),
            timeout=REQUEST_TIMEOUT_S,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        raise ESCOError(str(e)) from e


def _pick_label(item: dict[str, Any]) -> str | None:
    for key in ("preferredLabel", "title", "label", "name"):
        v = item.get(key)
        if isinstance(v, str) and v.strip():
            return v.strip()
        if isinstance(v, dict):
            for vv in v.values():
                if isinstance(vv, str) and vv.strip():
                    return vv.strip()
    return None


def _pick_uri(item: dict[str, Any]) -> str | None:
    v = item.get("uri")
    if isinstance(v, str) and v.strip():
        return v.strip()
    links = item.get("_links") or {}
    self_link = links.get("self") or {}
    href = self_link.get("href")
    if isinstance(href, str) and href.strip():
        return href.strip()
    return None


def _extract_results(payload: dict[str, Any]) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    if isinstance(payload.get("results"), list):
        return payload["results"]
    emb = payload.get("_embedded") or {}
    for key in (
        "results",
        "result",
        "occupations",
        "occupation",
        "skills",
        "skill",
        "concepts",
        "concept",
    ):
        if isinstance(emb.get(key), list):
            return emb[key]
    for v in emb.values():
        if isinstance(v, list) and v and isinstance(v[0], dict):
            return v
    return []


def search_occupations(
    query: str, language: str = "en", limit: int = 10, offset: int = 0
) -> list[dict[str, str]]:
    url = f"{ESCO_BASE_URL}/search"
    params = {
        "text": query,
        "type": "occupation",
        "language": language,
        "limit": limit,
        "offset": offset,
    }
    data = _get(url, params=params, language=language)
    results = _extract_results(data)
    out: list[dict[str, str]] = []
    for it in results:
        if not isinstance(it, dict):
            continue
        label = _pick_label(it) or query
        uri = _pick_uri(it) or ""
        if uri:
            out.append({"label": label, "uri": uri})
    return out


def search_skills(
    query: str, language: str = "en", limit: int = 15, offset: int = 0
) -> list[dict[str, str]]:
    url = f"{ESCO_BASE_URL}/search"
    params = {
        "text": query,
        "type": "skill",
        "language": language,
        "limit": limit,
        "offset": offset,
    }
    data = _get(url, params=params, language=language)
    results = _extract_results(data)
    out: list[dict[str, str]] = []
    for it in results:
        if not isinstance(it, dict):
            continue
        label = _pick_label(it) or query
        uri = _pick_uri(it) or ""
        if uri:
            out.append({"label": label, "uri": uri})
    return out


def get_occupation(uri: str, language: str = "en") -> dict[str, Any]:
    url = f"{ESCO_BASE_URL}/resource/occupation"
    return _get(url, params={"uri": uri, "language": language}, language=language)


def _fetch_hal_collection(
    href: str, language: str = "en", limit: int = 50
) -> list[dict[str, Any]]:
    if href.startswith("/"):
        href = ESCO_BASE_URL.rstrip("/") + href
    data = _get(href, params={"limit": limit}, language=language)
    return _extract_results(data)


def occupation_related_skills(
    occupation_uri: str, language: str = "en", max_items: int = 25
) -> list[str]:
    occ = get_occupation(occupation_uri, language=language)
    skills: list[str] = []

    emb = occ.get("_embedded") or {}
    for key, value in emb.items():
        if "skill" in str(key).lower() and isinstance(value, list):
            for it in value:
                if isinstance(it, dict):
                    label = _pick_label(it)
                    if label:
                        skills.append(label)

    links = occ.get("_links") or {}
    for key, meta in links.items():
        if "skill" not in str(key).lower():
            continue
        href = None
        if isinstance(meta, dict):
            href = meta.get("href")
        elif isinstance(meta, list) and meta and isinstance(meta[0], dict):
            href = meta[0].get("href")
        if isinstance(href, str) and href:
            try:
                for it in _fetch_hal_collection(href, language=language):
                    if isinstance(it, dict):
                        label = _pick_label(it)
                        if label:
                            skills.append(label)
            except ESCOError:
                continue

    seen = set()
    uniq: list[str] = []
    for s in skills:
        k = s.lower()
        if k in seen:
            continue
        seen.add(k)
        uniq.append(s)
        if len(uniq) >= max_items:
            break
    return uniq


def encode_uri(uri: str) -> str:
    return urllib.parse.quote(uri, safe="")
