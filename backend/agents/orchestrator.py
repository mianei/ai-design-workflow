"""Agent orchestration — sequential workflow with step tracking."""
from __future__ import annotations

import asyncio
import json
from datetime import datetime
from typing import Any, Callable

from sqlalchemy.orm import Session

from backend.agents.brief_agent import BriefAgent
from backend.agents.concept_agent import ConceptAgent
from backend.agents.insight_agent import InsightAgent
from backend.agents.requirement_agent import RequirementAgent
from backend.agents.research_agent import ResearchAgent
from backend.agents.sketch_agent import SketchAgent
from backend.config import PIPELINE_AGENT_TIMEOUT_SECONDS
from backend.database.models import AgentStep, Concept, DecisionEvent, Project

PIPELINE = [
    RequirementAgent(),
    ResearchAgent(),
    InsightAgent(),
    ConceptAgent(),
    SketchAgent(),
]


def _upsert_step(
    db: Session,
    project_id: int,
    agent_name: str,
    status: str,
    message: str = "",
    output: dict[str, Any] | None = None,
) -> AgentStep:
    step = (
        db.query(AgentStep)
        .filter(AgentStep.project_id == project_id, AgentStep.agent_name == agent_name)
        .first()
    )
    if not step:
        step = AgentStep(project_id=project_id, agent_name=agent_name)
        db.add(step)

    step.status = status
    step.message = message
    if status == "running":
        step.started_at = datetime.utcnow()
        step.completed_at = None
    if status in {"completed", "failed"}:
        step.completed_at = datetime.utcnow()
    if output is not None:
        step.output_json = json.dumps(output, ensure_ascii=False)
    db.commit()
    db.refresh(step)
    return step


def _log_decision(
    db: Session,
    project_id: int,
    event_type: str,
    actor: str,
    payload: dict[str, Any],
) -> None:
    db.add(
        DecisionEvent(
            project_id=project_id,
            event_type=event_type,
            actor=actor,
            payload_json=json.dumps(payload, ensure_ascii=False),
        )
    )
    db.commit()


def _preserve_concept_meta(db: Session, project_id: int) -> dict[str, dict[str, Any]]:
    """Keep human decisions (favorite/rating/keywords) across concept regeneration."""
    meta: dict[str, dict[str, Any]] = {}
    for row in db.query(Concept).filter(Concept.project_id == project_id).all():
        meta[row.concept_key] = {
            "is_favorite": row.is_favorite,
            "rating": row.rating,
            "edited_keywords_json": row.edited_keywords_json,
            "merged_from": row.merged_from,
        }
    return meta


def _replace_concepts(
    db: Session,
    project: Project,
    concepts: list[dict[str, Any]],
    *,
    preserve_meta: bool = True,
) -> None:
    meta = _preserve_concept_meta(db, project.id) if preserve_meta else {}
    db.query(Concept).filter(Concept.project_id == project.id).delete()
    for c in concepts:
        key = c["id"]
        prev = meta.get(key, {})
        body = dict(c)
        if prev.get("edited_keywords_json"):
            try:
                edited = json.loads(prev["edited_keywords_json"])
                if edited:
                    body["design_keywords"] = edited
            except json.JSONDecodeError:
                pass
        row = Concept(
            project_id=project.id,
            concept_key=key,
            concept_json=json.dumps(body, ensure_ascii=False),
            is_favorite=prev.get("is_favorite") or 0,
            rating=prev.get("rating"),
            edited_keywords_json=prev.get("edited_keywords_json"),
            merged_from=prev.get("merged_from"),
        )
        db.add(row)
    project.concepts_json = json.dumps({"concepts": concepts}, ensure_ascii=False)


def invalidate_brief_after_research(db: Session, project: Project) -> None:
    """Clear outdated brief when research/concepts are regenerated."""
    if project.brief_json or project.selected_concept_id or project.status in {
        "brief_ready",
        "decided",
    }:
        _log_decision(
            db,
            project.id,
            "brief_invalidated",
            "ai",
            {
                "reason": "research_rerun",
                "previous_selected_concept_id": project.selected_concept_id,
            },
        )
    project.brief_json = None
    project.selected_concept_id = None


async def run_research_pipeline(
    db: Session,
    project: Project,
    should_continue: Callable[[], bool] | None = None,
) -> Project:
    """Run agents 1-5: requirement → research → insight → concepts → sketches."""
    cont: Callable[[], bool] = should_continue or (lambda: True)

    invalidate_brief_after_research(db, project)
    project.status = "running"
    db.commit()

    context: dict[str, Any] = {
        "raw_input": project.raw_input,
        "project_id": project.id,
    }

    for agent in PIPELINE:
        if not cont():
            print(f"[pipeline] project {project.id} superseded — stop before {agent.name}")
            return project

        _upsert_step(db, project.id, agent.name, "running", f"{agent.name} running...")
        try:
            if agent.name == "sketch":
                context["concepts"] = {"concepts": context.get("concepts_list") or []}
            output = await asyncio.wait_for(
                agent.run(context),
                timeout=PIPELINE_AGENT_TIMEOUT_SECONDS,
            )
        except Exception as exc:  # noqa: BLE001
            if not cont():
                return project
            message = str(exc)
            if isinstance(exc, asyncio.TimeoutError):
                message = f"Agent timed out after {PIPELINE_AGENT_TIMEOUT_SECONDS:.0f}s"
            _upsert_step(db, project.id, agent.name, "failed", message)
            project.status = "failed"
            project.updated_at = datetime.utcnow()
            db.commit()
            raise RuntimeError(message) from exc

        if not cont():
            print(f"[pipeline] project {project.id} superseded — discard {agent.name} result")
            return project

        _upsert_step(db, project.id, agent.name, "completed", agent.display_message, output)
        _log_decision(
            db,
            project.id,
            "ai_generated",
            "ai",
            {"agent": agent.name, "message": agent.display_message},
        )

        if agent.name == "requirement":
            project.requirement_json = json.dumps(output, ensure_ascii=False)
            context["requirement"] = output
        elif agent.name == "research":
            project.research_json = json.dumps(output, ensure_ascii=False)
            context["research"] = output
        elif agent.name == "insight":
            project.insight_json = json.dumps(output, ensure_ascii=False)
            context["insight"] = output
        elif agent.name == "concept":
            context["concepts_list"] = output.get("concepts", [])
            project.concepts_json = json.dumps(output, ensure_ascii=False)
        elif agent.name == "sketch":
            _replace_concepts(db, project, output.get("concepts", []), preserve_meta=True)

        project.updated_at = datetime.utcnow()
        db.commit()

    if not cont():
        return project

    project.status = "concepts_ready"
    db.commit()
    db.refresh(project)
    return project


async def generate_brief_for_concept(
    db: Session,
    project: Project,
    concept_key: str,
) -> Project:
    """Human selects a concept → Brief Agent generates editable brief."""
    concept_row = (
        db.query(Concept)
        .filter(Concept.project_id == project.id, Concept.concept_key == concept_key)
        .first()
    )
    if not concept_row:
        raise ValueError(f"Concept not found: {concept_key}")

    concept_data = json.loads(concept_row.concept_json)
    if concept_row.edited_keywords_json:
        edited = json.loads(concept_row.edited_keywords_json)
        if edited:
            concept_data["design_keywords"] = edited

    context = {
        "requirement": json.loads(project.requirement_json or "{}"),
        "insight": json.loads(project.insight_json or "{}"),
        "selected_concept": concept_data,
    }

    agent = BriefAgent()
    _upsert_step(db, project.id, agent.name, "running", "Generating design brief...")
    project.status = "running"
    db.commit()
    try:
        brief = await asyncio.wait_for(
            agent.run(context),
            timeout=PIPELINE_AGENT_TIMEOUT_SECONDS,
        )
    except Exception as exc:  # noqa: BLE001
        message = str(exc)
        if isinstance(exc, asyncio.TimeoutError):
            message = f"Brief timed out after {PIPELINE_AGENT_TIMEOUT_SECONDS:.0f}s"
        _upsert_step(db, project.id, agent.name, "failed", message)
        project.status = "concepts_ready"
        db.commit()
        raise RuntimeError(message) from exc

    _upsert_step(db, project.id, agent.name, "completed", agent.display_message, brief)
    project.brief_json = json.dumps(brief, ensure_ascii=False)
    project.selected_concept_id = concept_key
    project.status = "brief_ready"
    project.updated_at = datetime.utcnow()
    db.commit()

    _log_decision(
        db,
        project.id,
        "select_brief",
        "user",
        {"concept_key": concept_key, "concept_name": concept_data.get("concept_name")},
    )
    _log_decision(
        db,
        project.id,
        "ai_generated",
        "ai",
        {"agent": "brief", "message": agent.display_message},
    )
    db.refresh(project)
    return project
