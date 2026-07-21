"""SQLAlchemy models for projects, workflow runs, and decision history."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    raw_input: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="draft")
    # draft | running | concepts_ready | brief_ready | decided
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    requirement_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    research_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    insight_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    concepts_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    brief_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    selected_concept_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    agent_steps: Mapped[list["AgentStep"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    concepts: Mapped[list["Concept"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    decisions: Mapped[list["DecisionEvent"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )


class AgentStep(Base):
    __tablename__ = "agent_steps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    agent_name: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="pending")
    # pending | running | completed | failed
    message: Mapped[str] = mapped_column(String(300), default="")
    output_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    project: Mapped["Project"] = relationship(back_populates="agent_steps")


class Concept(Base):
    __tablename__ = "concepts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    concept_key: Mapped[str] = mapped_column(String(64), nullable=False)
    concept_json: Mapped[str] = mapped_column(Text, nullable=False)
    is_favorite: Mapped[int] = mapped_column(Integer, default=0)
    rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    edited_keywords_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    merged_from: Mapped[str | None] = mapped_column(String(200), nullable=True)

    project: Mapped["Project"] = relationship(back_populates="concepts")


class DecisionEvent(Base):
    __tablename__ = "decision_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    # ai_generated | user_edit | favorite | rate | merge | select_brief | finalize
    actor: Mapped[str] = mapped_column(String(40), default="user")  # ai | user
    payload_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    project: Mapped["Project"] = relationship(back_populates="decisions")
