from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


WorkspaceTreeNodeKind = Literal["domain", "document", "section", "page", "chunk", "asset"]


class WorkspaceTreeNode(BaseModel):
    id: str
    kind: WorkspaceTreeNodeKind
    title: str
    children: list[WorkspaceTreeNode] = Field(default_factory=list)

    document_id: str | None = None
    section_id: str | None = None
    page_number: int | None = None
    chunk_id: str | None = None
    asset_id: str | None = None

    status: str | None = None
    filename: str | None = None
    content_type: str | None = None
    page_start: int | None = None
    page_end: int | None = None
    asset_type: str | None = None
    thumbnail_url: str | None = None
    metadata: dict = Field(default_factory=dict)


class WorkspaceTreeResponse(BaseModel):
    domain_id: str
    display_name: str | None = None
    document_count: int
    root: WorkspaceTreeNode
