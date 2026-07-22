"""Validate structured agent outputs (no silent mock fill in real mode)."""
from __future__ import annotations

from typing import Any


def require_object(result: Any, mock: dict[str, Any], *, use_mock: bool, required: list[str]) -> dict[str, Any]:
    if use_mock:
        base = dict(mock)
        if isinstance(result, dict):
            base.update({k: v for k, v in result.items() if v not in (None, "", [])})
        return base

    if not isinstance(result, dict):
        raise ValueError("LLM output must be a JSON object")

    missing = [k for k in required if result.get(k) in (None, "", [])]
    if missing:
        raise ValueError(f"LLM output missing required fields: {', '.join(missing)}")
    return result


def require_list(value: Any, *, field: str, min_items: int = 1) -> list[Any]:
    if not isinstance(value, list) or len(value) < min_items:
        raise ValueError(f"Field '{field}' must be a list with at least {min_items} item(s)")
    return value


def normalize_concepts(raw: Any, *, use_mock: bool, mock_concepts: list[dict[str, Any]], persona_name: str = "") -> list[dict[str, Any]]:
    if use_mock:
        concepts = []
        if isinstance(raw, dict) and isinstance(raw.get("concepts"), list):
            concepts = raw["concepts"]
        elif isinstance(raw, list):
            concepts = raw
        if len(concepts) < 3:
            concepts = list(concepts) + mock_concepts[len(concepts) : 3]
        concepts = concepts[:3]
    else:
        if not isinstance(raw, dict) or not isinstance(raw.get("concepts"), list):
            raise ValueError("LLM output must include concepts[]")
        concepts = raw["concepts"]
        if len(concepts) < 3:
            raise ValueError("LLM must return at least 3 concepts")
        concepts = concepts[:3]

    default_ids = ["concept_a", "concept_b", "concept_c"]
    normalized = []
    for i, c in enumerate(concepts):
        if not isinstance(c, dict):
            raise ValueError(f"concepts[{i}] must be an object")
        cid = c.get("id") or default_ids[i]
        name = c.get("concept_name")
        if not use_mock and not name:
            raise ValueError(f"concepts[{i}].concept_name is required")
        keywords = c.get("design_keywords") or []
        features = c.get("product_features") or []
        if not use_mock:
            require_list(keywords, field=f"concepts[{i}].design_keywords", min_items=1)
            require_list(features, field=f"concepts[{i}].product_features", min_items=1)
            if not c.get("visual_direction"):
                raise ValueError(f"concepts[{i}].visual_direction is required")
        normalized.append(
            {
                "id": cid,
                "concept_name": name or f"Concept {chr(65 + i)}",
                "target_user": c.get("target_user") or persona_name,
                "design_keywords": keywords if isinstance(keywords, list) else [],
                "product_features": features if isinstance(features, list) else [],
                "visual_direction": c.get("visual_direction") or "",
                "business_value": c.get("business_value") or "",
            }
        )
    return normalized
