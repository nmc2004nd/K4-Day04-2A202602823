from __future__ import annotations

import json
from typing import Any

from tools._shared import ROOT, err, terms


CATALOG_FILE = ROOT / "helpdesk_data" / "approved_software_catalog.json"

VALID_TEAMS = {
    "all",
    "engineering",
    "sales",
    "design",
    "finance",
    "operations",
    "executive",
    "hr",
    "support",
    "legal",
    "product",
}
VALID_OS_FAMILIES = {"all", "windows", "macos", "linux", "ios"}
VALID_CATEGORIES = {
    "all",
    "browser",
    "communication",
    "data",
    "design",
    "development",
    "productivity",
    "security",
    "vpn",
}


def _normalize(value: str, allowed: set[str], default: str | None = None) -> str:
    normalized = (value or default or "").strip().lower().replace(" ", "_")
    aliases = {
        "mac": "macos",
        "osx": "macos",
        "os_x": "macos",
        "win": "windows",
        "windows_11": "windows",
        "ubuntu": "linux",
        "human_resources": "hr",
    }
    normalized = aliases.get(normalized, normalized)
    return normalized if normalized in allowed else normalized


def approved_software_catalog(
    team: str = "",
    os_family: str = "",
    category: str = "all",
    software_name: str = "",
) -> dict[str, Any]:
    try:
        team_key = _normalize(team, VALID_TEAMS)
        os_key = _normalize(os_family, VALID_OS_FAMILIES)
        category_key = _normalize(category, VALID_CATEGORIES, "all")
        name_terms = terms(software_name)

        missing_fields = [
            field
            for field, value in (("team", team_key), ("os_family", os_key))
            if not value
        ]
        if missing_fields:
            return {
                "tool": "approved_software_catalog",
                "error": "missing_required_fields",
                "missing_fields": missing_fields,
            }
        if team_key not in VALID_TEAMS:
            return {"tool": "approved_software_catalog", "team": team_key, "error": "invalid_team"}
        if os_key not in VALID_OS_FAMILIES:
            return {"tool": "approved_software_catalog", "os_family": os_key, "error": "invalid_os_family"}
        if category_key not in VALID_CATEGORIES:
            return {
                "tool": "approved_software_catalog",
                "category": category_key,
                "error": "invalid_category",
            }

        data = json.loads(CATALOG_FILE.read_text(encoding="utf-8"))
        matches: list[dict[str, Any]] = []
        for item in data["catalog"]:
            if category_key != "all" and item["category"] != category_key:
                continue
            if team_key != "all" and "all" not in item["teams"] and team_key not in item["teams"]:
                continue
            if os_key != "all" and "all" not in item["os_families"] and os_key not in item["os_families"]:
                continue
            if name_terms:
                haystack = " ".join([item["name"], item["software_id"], item["category"], item["notes"]])
                if not name_terms & terms(haystack):
                    continue
            matches.append(item)

        return {
            "tool": "approved_software_catalog",
            "team": team_key,
            "os_family": os_key,
            "category": category_key,
            "software_name": software_name,
            "results": matches,
            "count": len(matches),
            "snapshot_at": data["snapshot_at"],
            "source": "fictional_internal_software_catalog",
        }
    except Exception as exc:
        return err("approved_software_catalog", exc)
