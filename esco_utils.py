# esco_utils.py - ESCO API integration for skill suggestions
from __future__ import annotations

from typing import Any

import requests


def fetch_essential_skills(job_title: str, language: str = "en") -> list[str]:
    """
    Fetch a list of essential skills for the given job title using the public ESCO API.
    Returns a list of skill names in the specified language (default English).
    """
    if not job_title:
        return []
    # Search for the occupation by title
    search_url = "https://ec.europa.eu/esco/api/search"
    params: dict[str, str] = {
        "text": job_title,
        "type": "occupation",
        "language": language,
        "limit": "1",
    }
    try:
        resp = requests.get(search_url, params=params, timeout=5)
        resp.raise_for_status()
    except Exception:
        # If any HTTP or network error occurs, return empty list
        return []
    data: dict[str, Any] = resp.json()
    results = data.get("_embedded", {}).get("results", [])
    if not results:
        return []
    # Take the first occupation match
    occupation_uri = results[0].get("uri")
    if not occupation_uri:
        return []
    # Fetch details for this occupation, including its essential skills
    detail_url = "https://ec.europa.eu/esco/api/resource/occupation"
    params = {"uri": occupation_uri, "language": language, "view": "full"}
    try:
        detail_resp = requests.get(detail_url, params=params, timeout=5)
        detail_resp.raise_for_status()
    except Exception:
        return []
    detail = detail_resp.json()
    skills = []
    for entry in detail.get("_links", {}).get("hasEssentialSkill", []) or []:
        label = entry.get("title")
        if label:
            skills.append(label.strip())
    # Remove duplicates, preserve order
    seen = set()
    unique_skills = []
    for skill in skills:
        if skill not in seen:
            unique_skills.append(skill)
            seen.add(skill)
    return unique_skills
