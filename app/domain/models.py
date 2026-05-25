from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID


class UserRole(StrEnum):
    ADMIN = "admin"
    USER = "user"


class DocumentStatus(StrEnum):
    UPLOADED = "uploaded"
    INDEXING = "indexing"
    READY = "ready"
    FAILED = "failed"
    DELETED = "deleted"


class RetrievalMode(StrEnum):
    AUTO = "auto"
    SEMANTIC = "semantic"
    NAVIGATION = "navigation"
    HYBRID = "hybrid"


class JobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"


@dataclass(frozen=True)
class User:
    id: UUID
    email: str
    role: UserRole
    is_active: bool = True


@dataclass(frozen=True)
class Document:
    id: UUID
    owner_id: UUID | None
    filename: str
    content_type: str
    storage_path: str
    status: DocumentStatus
    created_at: datetime
    updated_at: datetime
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PageRef:
    document_id: UUID
    page_start: int | None = None
    page_end: int | None = None


@dataclass(frozen=True)
class SectionRef:
    document_id: UUID
    section_id: str
    title: str
    page_start: int | None = None
    page_end: int | None = None


@dataclass(frozen=True)
class Evidence:
    id: str
    document_id: UUID
    source_engine: str
    text: str
    score: float | None = None
    page_ref: PageRef | None = None
    section_ref: SectionRef | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RetrievalResult:
    query: str
    mode: RetrievalMode
    evidence: list[Evidence]
    debug: dict[str, Any] = field(default_factory=dict)


def utc_now() -> datetime:
    return datetime.now(UTC)

