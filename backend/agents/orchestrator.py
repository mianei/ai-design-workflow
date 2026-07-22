"""Agent orchestration — sequential workflow with step tracking."""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from backend.agents.brief_agent import BriefAgent
from backend.agents.concept_agent import ConceptAgent
from backend.agents.insight_agent import InsightAgent
from backend.agents.requirement_agent import RequirementAgent
from backend.agents.research_agent import ResearchAgent
from backend.agents.sketch_agent import SketchAgent
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


async def run_research_pipeline(
    db: Session,
    project: Project,
    should_continue: Any | None = None,
) -> Project:
    """Run agents 1-4: requirement → research → insight → concepts."""
    from collections.abc import Callable

    cont: Callable[[], bool] = should_continue or (lambda: True)

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
            # Sketch agent needs concepts from previous step
            if agent.name == "sketch":
                context["concepts"] = {"concepts": context.get("concepts_list") or []}
            output = await agent.run(context)
        except Exception as exc:  # noqa: BLE001
            if not cont():
                return project
            _upsert_step(db, project.id, agent.name, "failed", str(exc))
            project.status = "draft"
            db.commit()
            raise

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
            concepts = output.get("concepts", [])
            project.concepts_json = json.dumps({"concepts": concepts}, ensure_ascii=False)
            db.query(Concept).filter(Concept.project_id == project.id).delete()
            for c in concepts:
                db.add(
                    Concept(
                        project_id=project.id,
                        concept_key=c["id"],
                        concept_json=json.dumps(c, ensure_ascii=False),
                    )
                )

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
    try:
        brief = await agent.run(context)
    except Exception as exc:  # noqa: BLE001
        _upsert_step(db, project.id, agent.name, "failed", str(exc))
        raise

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
