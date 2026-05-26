from app.integrations.lightrag_graph_mapper import (
    to_graph_label_search_response,
    to_graph_labels_response,
    to_graph_response,
)


def test_to_graph_response_normalizes_nodes_and_edges() -> None:
    payload = {
        "nodes": [
            {
                "id": "n1",
                "labels": ["Pump"],
                "properties": {"entity_id": "Pump", "entity_type": "equipment", "extra": 1},
            },
            {"id": None, "labels": ["broken"], "properties": {}},
        ],
        "edges": [
            {
                "id": "e1",
                "source": "n1",
                "target": "n2",
                "type": "connects",
                "properties": {"weight": "2.5", "description": "connects to", "extra": "ok"},
            },
            {"id": "bad", "source": "n1"},
        ],
        "is_truncated": True,
    }

    response = to_graph_response(payload)

    assert response.truncated is True
    assert len(response.nodes) == 1
    assert response.nodes[0].id == "n1"
    assert response.nodes[0].display_label == "Pump"
    assert response.nodes[0].entity_type == "equipment"
    assert response.nodes[0].properties == {"entity_id": "Pump", "entity_type": "equipment", "extra": 1}
    assert len(response.edges) == 1
    assert response.edges[0].id == "e1"
    assert response.edges[0].relation == "connects"
    assert response.edges[0].weight == 2.5
    assert response.edges[0].description == "connects to"


def test_to_graph_response_defaults_when_payload_shape_is_invalid() -> None:
    response = to_graph_response({"nodes": "invalid", "edges": None})
    assert response.nodes == []
    assert response.edges == []
    assert response.truncated is False


def test_to_graph_labels_response_accepts_list_or_dict_payloads() -> None:
    list_response = to_graph_labels_response(["A", "B", 3, "", None])
    dict_response = to_graph_labels_response({"labels": ["A", "B"]})

    assert list_response.labels == ["A", "B", "3"]
    assert dict_response.labels == ["A", "B"]


def test_to_graph_label_search_response_carries_query_and_limit() -> None:
    response = to_graph_label_search_response(
        {"data": ["pump", "valve", "", None]},
        query="p",
        limit=10,
    )

    assert response.query == "p"
    assert response.limit == 10
    assert response.labels == ["pump", "valve"]
