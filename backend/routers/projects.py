"""Project and workflow API routes."""
from __future__ import annotations

import json
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from backend.agents.orchestrator import generate_brief_for_concept, run_research_pipeline
from backend.database.db import SessionLocal, get_db
from backend.database.models import Concept, DecisionEvent, Project
from backend.schemas import (
    BriefUpdate,
    ConceptUpdate,
    FinalizeRequest,
    MergeConceptsRequest,
    ProjectCreate,
    SelectConceptRequest,
    serialize_project,
)

router = APIRouter(prefix="/api")

# Per-project run generation — force rerun bumps the token so old background jobs exit.
_run_generation: dict[int, int] = {}


def _get_project(db: Session, project_id: int) -> Project:
    project = (
        db.query(Project)
        .options(
            joinedload(Project.agent_steps),
            joinedload(Project.concepts),
            joinedload(Project.decisions),
        )
        .filter(Project.id == project_id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def _next_generation(project_id: int) -> int:
    _run_generation[project_id] = _run_generation.get(project_id, 0) + 1
    return _run_generation[project_id]


def _current_generation(project_id: int) -> int:
    return _run_generation.get(project_id, 0)


async def _background_pipeline(project_id: int, generation: int) -> None:
    db = SessionLocal()
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return
        try:
            await run_research_pipeline(
                db,
                project,
                should_continue=lambda: _current_generation(project_id) == generation,
            )
        except Exception as exc:  # noqa: BLE001
            print(f"[pipeline] project {project_id} failed: {exc}")
            if _current_generation(project_id) != generation:
                return
            project = db.query(Project).filter(Project.id == project_id).first()
            if project and project.status == "running":
                project.status = "draft"
                db.commit()
    finally:
        db.close()


def _mark_project_running(db: Session, project: Project) -> None:
    project.status = "running"
    project.updated_at = datetime.utcnow()
    db.commit()


@router.get("/health")
def health():
    from backend.config import LLM_MODEL, LLM_PROVIDER, use_mock_llm

    return {
        "status": "ok",
        "llm_provider": LLM_PROVIDER,
        "llm_model": LLM_MODEL,
        "mock_mode": use_mock_llm(),
    }


@router.get("/projects")
def list_projects(db: Session = Depends(get_db)):
    projects = db.query(Project).order_by(Project.updated_at.desc()).all()
    return [serialize_project(p, include_details=False) for p in projects]


@router.post("/projects")
async def create_project(
    payload: ProjectCreate,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
):
    project = Project(title=payload.title, raw_input=payload.raw_input, status="running")
    db.add(project)
    db.commit()
    db.refresh(project)

    db.add(
        DecisionEvent(
            project_id=project.id,
            event_type="project_created",
            actor="user",
            payload_json=json.dumps({"title": project.title}, ensure_ascii=False),
        )
    )
    db.commit()

    background.add_task(_background_pipeline, project.id, _next_generation(project.id))
    project = _get_project(db, project.id)
    return serialize_project(project)


@router.get("/projects/{project_id}")
def get_project(project_id: int, db: Session = Depends(get_db)):
    return serialize_project(_get_project(db, project_id))


@router.post("/projects/{project_id}/rerun")
async def rerun_pipeline(
    project_id: int,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
    force: bool = True,
):
    """Restart research pipeline. Default force=True so stuck 'running' jobs can recover."""
    from backend.database.models import AgentStep

    project = _get_project(db, project_id)
    if project.status == "running" and not force:
        raise HTTPException(status_code=409, detail="Pipeline already running")

    # Reset step statuses so UI shows a fresh run
    for step in db.query(AgentStep).filter(AgentStep.project_id == project_id).all():
        step.status = "pending"
        step.message = "Waiting to restart"
        step.started_at = None
        step.completed_at = None
    _mark_project_running(db, project)
    gen = _next_generation(project_id)
    background.add_task(_background_pipeline, project.id, gen)
    return {"ok": True, "status": "running", "forced": force}


@router.patch("/projects/{project_id}/concepts/{concept_key}")
def update_concept(
    project_id: int,
    concept_key: str,
    payload: ConceptUpdate,
    db: Session = Depends(get_db),
):
    project = _get_project(db, project_id)
    concept = (
        db.query(Concept)
        .filter(Concept.project_id == project_id, Concept.concept_key == concept_key)
        .first()
    )
    if not concept:
        raise HTTPException(status_code=404, detail="Concept not found")

    events = []
    if payload.is_favorite is not None:
        concept.is_favorite = 1 if payload.is_favorite else 0
        events.append(("favorite", {"concept_key": concept_key, "is_favorite": payload.is_favorite}))
    if payload.rating is not None:
        concept.rating = payload.rating
        events.append(("rate", {"concept_key": concept_key, "rating": payload.rating}))
    if payload.design_keywords is not None:
        concept.edited_keywords_json = json.dumps(payload.design_keywords, ensure_ascii=False)
        # also sync into concept_json
        body = json.loads(concept.concept_json)
        body["design_keywords"] = payload.design_keywords
        concept.concept_json = json.dumps(body, ensure_ascii=False)
        events.append(
            ("user_edit", {"concept_key": concept_key, "design_keywords": payload.design_keywords})
        )

    for event_type, data in events:
        db.add(
            DecisionEvent(
                project_id=project.id,
                event_type=event_type,
                actor="user",
                payload_json=json.dumps(data, ensure_ascii=False),
            )
        )

    project.updated_at = datetime.utcnow()
    db.commit()
    return serialize_project(_get_project(db, project_id))


@router.post("/projects/{project_id}/concepts/merge")
def merge_concepts(
    project_id: int,
    payload: MergeConceptsRequest,
    db: Session = Depends(get_db),
):
    project = _get_project(db, project_id)
    a = (
        db.query(Concept)
        .filter(Concept.project_id == project_id, Concept.concept_key == payload.source_a)
        .first()
    )
    b = (
        db.query(Concept)
        .filter(Concept.project_id == project_id, Concept.concept_key == payload.source_b)
        .first()
    )
    if not a or not b:
        raise HTTPException(status_code=404, detail="Source concept(s) not found")

    ca = json.loads(a.concept_json)
    cb = json.loads(b.concept_json)
    keywords = list(dict.fromkeys((ca.get("design_keywords") or []) + (cb.get("design_keywords") or [])))
    features = list(dict.fromkeys((ca.get("product_features") or []) + (cb.get("product_features") or [])))
    merged_key = f"merged_{payload.source_a}_{payload.source_b}"
    merged_name = payload.concept_name or f"{ca.get('concept_name')} × {cb.get('concept_name')}"
    merged = {
        "id": merged_key,
        "concept_name": merged_name,
        "target_user": ca.get("target_user") or cb.get("target_user"),
        "design_keywords": keywords[:6],
        "product_features": features[:6],
        "visual_direction": f"{ca.get('visual_direction', '')} / {cb.get('visual_direction', '')}",
        "business_value": f"融合方向：{ca.get('business_value', '')}；{cb.get('business_value', '')}",
    }

    existing = (
        db.query(Concept)
        .filter(Concept.project_id == project_id, Concept.concept_key == merged_key)
        .first()
    )
    if existing:
        existing.concept_json = json.dumps(merged, ensure_ascii=False)
        existing.merged_from = f"{payload.source_a}+{payload.source_b}"
    else:
        db.add(
            Concept(
                project_id=project_id,
                concept_key=merged_key,
                concept_json=json.dumps(merged, ensure_ascii=False),
                merged_from=f"{payload.source_a}+{payload.source_b}",
            )
        )

    db.add(
        DecisionEvent(
            project_id=project_id,
            event_type="merge",
            actor="user",
            payload_json=json.dumps(
                {"source_a": payload.source_a, "source_b": payload.source_b, "merged_key": merged_key},
                ensure_ascii=False,
            ),
        )
    )
    project.updated_at = datetime.utcnow()
    db.commit()
    return serialize_project(_get_project(db, project_id))


@router.post("/projects/{project_id}/brief/generate")
async def generate_brief(
    project_id: int,
    payload: SelectConceptRequest,
    db: Session = Depends(get_db),
):
    project = _get_project(db, project_id)
    if project.status == "running":
        raise HTTPException(status_code=409, detail="Research pipeline still running")
    try:
        project = await generate_brief_for_concept(db, project, payload.concept_key)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return serialize_project(_get_project(db, project.id))


@router.patch("/projects/{project_id}/brief")
def update_brief(project_id: int, payload: BriefUpdate, db: Session = Depends(get_db)):
    project = _get_project(db, project_id)
    if not project.brief_json:
        raise HTTPException(status_code=400, detail="No brief to edit — select a concept first")

    brief = json.loads(project.brief_json)
    updates = payload.model_dump(exclude_none=True)
    brief.update(updates)
    project.brief_json = json.dumps(brief, ensure_ascii=False)
    project.updated_at = datetime.utcnow()
    db.add(
        DecisionEvent(
            project_id=project_id,
            event_type="user_edit",
            actor="user",
            payload_json=json.dumps({"brief_fields": list(updates.keys())}, ensure_ascii=False),
        )
    )
    db.commit()
    return serialize_project(_get_project(db, project_id))


@router.post("/projects/{project_id}/finalize")
def finalize_project(
    project_id: int,
    payload: FinalizeRequest,
    db: Session = Depends(get_db),
):
    project = _get_project(db, project_id)
    if not project.brief_json or not project.selected_concept_id:
        raise HTTPException(
            status_code=400,
            detail="Cannot finalize: human must select a concept and generate a brief first",
        )
    project.status = "decided"
    project.updated_at = datetime.utcnow()
    db.add(
        DecisionEvent(
            project_id=project_id,
            event_type="finalize",
            actor="user",
            payload_json=json.dumps(
                {
                    "selected_concept_id": project.selected_concept_id,
                    "note": payload.note,
                    "message": "Final design brief confirmed by human",
                },
                ensure_ascii=False,
            ),
        )
    )
    db.commit()
    return serialize_project(_get_project(db, project_id))
