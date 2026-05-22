from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.domain.models import DocumentStatus, JobStatus, UserRole, utc_now
from app.storage.db import Base


def json_type():
    return JSON().with_variant(JSONB, "postgresql")


class UserRow(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(32), default=UserRole.USER.value)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class DocumentRow(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    owner_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    filename: Mapped[str] = mapped_column(String(512))
    content_type: Mapped[str] = mapped_column(String(255))
    storage_path: Mapped[str] = mapped_column(String(1024))
    status: Mapped[str] = mapped_column(String(32), default=DocumentStatus.UPLOADED.value)
    active_index_version: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    meta: Mapped[dict] = mapped_column("metadata", json_type(), default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class ParsedDocumentRow(Base):
    __tablename__ = "parsed_documents"

    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("documents.id"), primary_key=True)
    title: Mapped[str] = mapped_column(String(512))
    pages: Mapped[list] = mapped_column(json_type(), default=list)
    full_text: Mapped[str] = mapped_column(Text)
    meta: Mapped[dict] = mapped_column("metadata", json_type(), default=dict)


class NavigationIndexRow(Base):
    __tablename__ = "navigation_indexes"

    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("documents.id"), primary_key=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    tree: Mapped[list] = mapped_column(json_type(), default=list)


class DocumentSectionRow(Base):
    __tablename__ = "document_sections"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("documents.id"), index=True)
    parent_section_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    title: Mapped[str] = mapped_column(String(512))
    level: Mapped[int] = mapped_column(Integer)
    page_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    page_end: Mapped[int | None] = mapped_column(Integer, nullable=True)
    block_ids: Mapped[list] = mapped_column(json_type(), default=list)
    child_section_ids: Mapped[list] = mapped_column(json_type(), default=list)
    source: Mapped[str] = mapped_column(String(32), default="docling")
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)


class DocumentBlockRow(Base):
    __tablename__ = "document_blocks"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("documents.id"), index=True)
    section_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    type: Mapped[str] = mapped_column(String(32))
    text: Mapped[str] = mapped_column(Text, default="")
    page_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    page_end: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bbox: Mapped[dict | None] = mapped_column(json_type(), nullable=True)
    reading_order: Mapped[int | None] = mapped_column(Integer, nullable=True)
    asset_ids: Mapped[list] = mapped_column(json_type(), default=list)


class DocumentSourceChunkRow(Base):
    __tablename__ = "document_source_chunks"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("documents.id"), index=True)
    section_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    block_ids: Mapped[list] = mapped_column(json_type(), default=list)
    text: Mapped[str] = mapped_column(Text)
    page_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    page_end: Mapped[int | None] = mapped_column(Integer, nullable=True)
    asset_ids: Mapped[list] = mapped_column(json_type(), default=list)
    meta: Mapped[dict] = mapped_column("metadata", json_type(), default=dict)


class DocumentAssetRow(Base):
    __tablename__ = "document_assets"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("documents.id"), index=True)
    section_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    block_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    chunk_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    asset_type: Mapped[str] = mapped_column(String(32))
    storage_path: Mapped[str] = mapped_column(String(1024))
    thumbnail_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    mime_type: Mapped[str] = mapped_column(String(128), default="image/png")
    content_hash: Mapped[str] = mapped_column(String(128))
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    caption: Mapped[str | None] = mapped_column(Text, nullable=True)
    nearby_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    bbox: Mapped[dict | None] = mapped_column(json_type(), nullable=True)
    generated_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    ocr_text: Mapped[str | None] = mapped_column(Text, nullable=True)


class TocRefinementReportRow(Base):
    __tablename__ = "toc_refinement_reports"

    id: Mapped[str] = mapped_column(String(128), primary_key=True, default=lambda: str(uuid4()))
    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("documents.id"), index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    accepted: Mapped[bool] = mapped_column(Boolean, default=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    validation_accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)
    logical_to_physical_offset: Mapped[int | None] = mapped_column(Integer, nullable=True)
    llm_call_count: Mapped[int] = mapped_column(Integer, default=0)
    warnings: Mapped[list] = mapped_column(json_type(), default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class JobRow(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    kind: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32), default=JobStatus.QUEUED.value)
    document_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("documents.id"), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    meta: Mapped[dict] = mapped_column("metadata", json_type(), default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class AuditLogRow(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    actor_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    event: Mapped[str] = mapped_column(String(128))
    target_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    meta: Mapped[dict] = mapped_column("metadata", json_type(), default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class QueryLogRow(Base):
    __tablename__ = "query_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    query: Mapped[str] = mapped_column(Text)
    mode: Mapped[str] = mapped_column(String(32))
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    evidence_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

