from typing import Literal

from pydantic import BaseModel, Field


WorkspaceContextNodeKind = Literal["domain", "document", "section", "page", "chunk", "asset"]


class WorkspaceContextBreadcrumbItem(BaseModel):
    id: str | None = None
    kind: WorkspaceContextNodeKind | str
    title: str


class WorkspaceContextDocument(BaseModel):
    document_id: str
    title: str
    filename: str | None = None
    content_type: str | None = None
    status: str | None = None
    source_path: str | None = None


class WorkspaceContextAsset(BaseModel):
    asset_id: str
    document_id: str
    asset_type: str
    title: str
    caption: str | None = None
    page_number: int | None = None
    section_id: str | None = None
    url: str | None = None
    thumbnail_url: str | None = None
    mime_type: str | None = None
    metadata: dict = Field(default_factory=dict)


class WorkspaceSourceContext(BaseModel):
    node_id: str
    kind: WorkspaceContextNodeKind
    title: str
    domain_id: str
    breadcrumb: list[WorkspaceContextBreadcrumbItem] = Field(default_factory=list)
    document: WorkspaceContextDocument | None = None
    section_id: str | None = None
    page_number: int | None = None
    page_start: int | None = None
    page_end: int | None = None
    chunk_id: str | None = None
    asset_id: str | None = None
    summary: str | None = None
    text: str | None = None
    assets: list[WorkspaceContextAsset] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
