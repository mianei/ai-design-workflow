"""API schemas and serialization helpers."""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from backend.database.models import Concept, DecisionEvent, Project


class ProjectCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    raw_input: str = Field(..., min_length=1)


class ConceptUpdate(BaseModel):
    is_favorite: bool | None = None
    rating: float | None = None
    design_keywords: list[str] | None = None


class MergeConceptsRequest(BaseModel):
    source_a: str
    source_b: str
    concept_name: str | None = None


class SelectConceptRequest(BaseModel):
    concept_key: str


class BriefUpdate(BaseModel):
    design_goal: str | None = None
    target_user: str | None = None
    design_keywords: list[str] | None = None
    CMF_direction: str | None = None
    form_language: str | None = None
    must_have_features: str | None = None
    avoid_features: str | None = None


class FinalizeRequest(BaseModel):
    note: str | None = None


def _loads(raw: str | None) -> Any:
    if not raw:
        return None
    return json.loads(raw)


def serialize_project(project: Project, include_details: bool = True) -> dict[str, Any]:
    data: dict[str, Any] = {
        "id": project.id,
        "title": project.title,
        "raw_input": project.raw_input,
        "status": project.status,
        "selected_concept_id": project.selected_concept_id,
        "created_at": _dt(project.created_at),
        "updated_at": _dt(project.updated_at),
    }
    if not include_details:
        return data

    steps = sorted(project.agent_steps, key=lambda s: s.id)
    concepts = [_serialize_concept(c) for c in project.concepts]
    decisions = [_serialize_decision(d) for d in sorted(project.decisions, key=lambda x: x.id)]

    data.update(
        {
            "requirement": _loads(project.requirement_json),
            "research": _loads(project.research_json),
            "insight": _loads(project.insight_json),
            "concepts": concepts,
            "brief": _loads(project.brief_json),
            "agent_steps": [
                {
                    "agent_name": s.agent_name,
                    "status": s.status,
                    "message": s.message,
                    "started_at": _dt(s.started_at),
                    "completed_at": _dt(s.completed_at),
                }
                for s in steps
            ],
            "decisions": decisions,
        }
    )
    return data


def _serialize_concept(c: Concept) -> dict[str, Any]:
    body = json.loads(c.concept_json)
    edited = json.loads(c.edited_keywords_json) if c.edited_keywords_json else None
    if edited:
        body["design_keywords"] = edited
    return {
        **body,
        "id": body.get("id", c.concept_key),
        "concept_key": c.concept_key,
        "is_favorite": bool(c.is_favorite),
        "rating": c.rating,
        "merged_from": c.merged_from,
    }


def _serialize_decision(d: DecisionEvent) -> dict[str, Any]:
    return {
        "id": d.id,
        "event_type": d.event_type,
        "actor": d.actor,
        "payload": _loads(d.payload_json) or {},
        "created_at": _dt(d.created_at),
    }


def _dt(value: datetime | None) -> str | None:
    return value.isoformat() + "Z" if value else None
