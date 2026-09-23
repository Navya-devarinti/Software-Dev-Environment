"""Relational models for the reviewed public PNW information corpus.

These models intentionally contain only public-source and public-office data.
They must not be used for student, account, session, or chat-history data.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from enum import Enum
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import Date, DateTime, Enum as SqlEnum, ForeignKey, JSON, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for the application's relational corpus models."""


class SourceVersionStatus(str, Enum):
    """Review states allowed for a captured source version."""

    CURRENT = "current"
    SUPERSEDED = "superseded"
    INCOMPLETE = "incomplete"
    UNREVIEWED = "unreviewed"


class Source(Base):
    """An approved official PNW page or document."""

    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(500))
    url: Mapped[str] = mapped_column(String(2048), unique=True)
    category: Mapped[str] = mapped_column(String(100))
    owner_office: Mapped[str] = mapped_column(String(255))
    authority_scope: Mapped[str | None] = mapped_column(Text, nullable=True)
    review_frequency: Mapped[str] = mapped_column(String(100))
    last_reviewed_on: Mapped[date] = mapped_column(Date)
    related_source_id: Mapped[int | None] = mapped_column(
        ForeignKey("sources.id"), nullable=True
    )

    related_source: Mapped["Source | None"] = relationship(
        back_populates="related_sources", remote_side="Source.id"
    )
    related_sources: Mapped[list["Source"]] = relationship(
        back_populates="related_source"
    )
    versions: Mapped[list["SourceVersion"]] = relationship(
        back_populates="source", cascade="all, delete-orphan"
    )


class SourceVersion(Base):
    """A reviewed capture of an approved source at a particular point in time."""

    __tablename__ = "source_versions"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), index=True)
    captured_on: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    published_or_updated_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    effective_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[SourceVersionStatus] = mapped_column(
        SqlEnum(
            SourceVersionStatus,
            name="source_version_status",
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
        ),
        default=SourceVersionStatus.UNREVIEWED,
    )
    source_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    source: Mapped[Source] = relationship(back_populates="versions")
    evidence: Mapped[list["Evidence"]] = relationship(
        back_populates="source_version", cascade="all, delete-orphan"
    )


class Evidence(Base):
    """A citable extracted passage from one exact reviewed source version."""

    __tablename__ = "evidence"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_version_id: Mapped[int] = mapped_column(
        ForeignKey("source_versions.id"), index=True
    )
    text: Mapped[str] = mapped_column(Text)
    locator: Mapped[str] = mapped_column(String(1000))
    context: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(768), nullable=True
    )

    source_version: Mapped[SourceVersion] = relationship(back_populates="evidence")


class OfficeRoute(Base):
    """An approved public office route for questions the app cannot answer."""

    __tablename__ = "office_routes"

    id: Mapped[int] = mapped_column(primary_key=True)
    category: Mapped[str] = mapped_column(String(100), index=True)
    scope: Mapped[str | None] = mapped_column(Text, nullable=True)
    office_name: Mapped[str] = mapped_column(String(255))
    contact_url: Mapped[str] = mapped_column(String(2048))
    source_url: Mapped[str] = mapped_column(String(2048))
