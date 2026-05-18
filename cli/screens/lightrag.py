"""LightRAG graph screen builders."""

from __future__ import annotations

from typing import Any

from cli.screens.models import ScreenAction, ScreenResult, ScreenSection


def build_labels_screen(labels: list[Any], *, title: str = "Labels") -> ScreenResult:
    rows = [
        {
            "#": index,
            **(item if isinstance(item, dict) else {"label": item}),
        }
        for index, item in enumerate(labels, start=1)
    ]
    columns = list(rows[0].keys()) if rows else ["#", "label"]
    return ScreenResult(
        title=title,
        api_group="lightrag",
        sections=[ScreenSection(title="", rows=rows, columns=columns)],
        actions=[ScreenAction("Show graph", "context-engine lightrag graphs show --label <label>")],
        raw=labels,
    )


def build_graph_screen(graph: dict[str, Any]) -> ScreenResult:
    nodes = graph.get("nodes") or []
    edges = graph.get("edges") or []
    label_counts: dict[str, int] = {}
    for node in nodes:
        for label in node.get("labels", []) if isinstance(node, dict) else []:
            label_counts[str(label)] = label_counts.get(str(label), 0) + 1
    top_labels = []
    for index, (label, count) in enumerate(
        sorted(label_counts.items(), key=lambda item: item[1], reverse=True)[:5],
        start=1,
    ):
        top_labels.append({"#": index, "label": label, "relationship": count})
    sections = [
        ScreenSection(
            title="Request",
            rows=[
                {"field": "Max depth", "value": graph.get("max_depth", "")},
                {"field": "Max nodes", "value": graph.get("max_nodes", "")},
            ],
            columns=["field", "value"],
        ),
        ScreenSection(
            title="Summary",
            rows=[
                {"field": "Nodes", "value": graph.get("node_count", len(nodes))},
                {"field": "Edges", "value": graph.get("edge_count", len(edges))},
                {"field": "Depth returned", "value": graph.get("depth_returned", "")},
            ],
            columns=["field", "value"],
        )
    ]
    if top_labels:
        sections.append(
            ScreenSection(
                title="Top connected labels",
                rows=top_labels,
                columns=["#", "label", "relationship"],
            )
        )
    return ScreenResult(
        title="LightRAG Graph",
        api_group="lightrag",
        summary={"label": graph.get("label", "")},
        sections=sections,
        actions=[ScreenAction("Export graph JSON", "context-engine lightrag graphs show --label <label> --output json")],
        raw=graph,
    )
