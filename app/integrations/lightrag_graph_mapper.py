from typing import Any

from app.schemas.lightrag_graph import (
    GraphEdge,
    GraphLabelSearchResponse,
    GraphLabelsResponse,
    GraphNode,
    GraphResponse,
)


def to_graph_response(payload: dict[str, Any] | list[Any]) -> GraphResponse:
    if not isinstance(payload, dict):
        return GraphResponse()
    node_items = payload.get("nodes")
    edge_items = payload.get("edges")
    nodes = _normalize_nodes(node_items if isinstance(node_items, list) else [])
    edges = _normalize_edges(edge_items if isinstance(edge_items, list) else [])
    truncated = bool(payload.get("is_truncated") or payload.get("truncated"))
    return GraphResponse(nodes=nodes, edges=edges, truncated=truncated)


def to_graph_labels_response(payload: dict[str, Any] | list[Any]) -> GraphLabelsResponse:
    return GraphLabelsResponse(labels=_normalize_labels(payload))


def to_graph_label_search_response(
    payload: dict[str, Any] | list[Any], *, query: str, limit: int
) -> GraphLabelSearchResponse:
    return GraphLabelSearchResponse(query=query, limit=limit, labels=_normalize_labels(payload))


def _normalize_nodes(nodes: list[Any]) -> list[GraphNode]:
    normalized: list[GraphNode] = []
    for node in nodes:
        if not isinstance(node, dict):
            continue
        node_id = _to_non_empty_string(node.get("id"))
        if not node_id:
            continue
        labels = _to_string_list(node.get("labels"))
        properties = node.get("properties")
        safe_properties = properties if isinstance(properties, dict) else {}
        display_label = _to_non_empty_string(
            safe_properties.get("entity_id") if isinstance(safe_properties, dict) else None
        ) or (labels[0] if labels else node_id)
        entity_type = _to_non_empty_string(
            safe_properties.get("entity_type") if isinstance(safe_properties, dict) else None
        )
        normalized.append(
            GraphNode(
                id=node_id,
                labels=labels,
                display_label=display_label,
                entity_type=entity_type,
                properties=safe_properties,
            )
        )
    return normalized


def _normalize_edges(edges: list[Any]) -> list[GraphEdge]:
    normalized: list[GraphEdge] = []
    for index, edge in enumerate(edges):
        if not isinstance(edge, dict):
            continue
        source = _to_non_empty_string(edge.get("source"))
        target = _to_non_empty_string(edge.get("target"))
        if not source or not target:
            continue
        edge_id = _to_non_empty_string(edge.get("id")) or f"{source}-{target}-{index}"
        properties = edge.get("properties")
        safe_properties = properties if isinstance(properties, dict) else {}
        relation = _to_non_empty_string(edge.get("type"))
        description = _to_non_empty_string(
            safe_properties.get("description") if isinstance(safe_properties, dict) else None
        )
        weight = _to_number(safe_properties.get("weight") if isinstance(safe_properties, dict) else None)
        normalized.append(
            GraphEdge(
                id=edge_id,
                source=source,
                target=target,
                relation=relation,
                description=description,
                weight=weight,
                properties=safe_properties,
            )
        )
    return normalized


def _normalize_labels(payload: dict[str, Any] | list[Any]) -> list[str]:
    if isinstance(payload, list):
        return _to_string_list(payload)
    if not isinstance(payload, dict):
        return []
    if isinstance(payload.get("labels"), list):
        return _to_string_list(payload.get("labels"))
    if isinstance(payload.get("data"), list):
        return _to_string_list(payload.get("data"))
    return []


def _to_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    labels: list[str] = []
    for item in value:
        text = _to_non_empty_string(item)
        if text:
            labels.append(text)
    return labels


def _to_non_empty_string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text if text else None


def _to_number(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
