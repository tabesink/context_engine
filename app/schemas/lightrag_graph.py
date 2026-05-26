from typing import Any

from pydantic import BaseModel, Field


class GraphNode(BaseModel):
    id: str
    labels: list[str] = Field(default_factory=list)
    display_label: str
    entity_type: str | None = None
    properties: dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    relation: str | None = None
    weight: float | None = None
    description: str | None = None
    properties: dict[str, Any] = Field(default_factory=dict)


class GraphResponse(BaseModel):
    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)
    truncated: bool = False


class GraphLabelsResponse(BaseModel):
    labels: list[str] = Field(default_factory=list)


class GraphLabelSearchResponse(BaseModel):
    query: str
    limit: int
    labels: list[str] = Field(default_factory=list)
