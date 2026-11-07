"""Contract tests for the FCose graph payload.

These tests read the committed mock payload, so they do not need a running
TypeDB instance. The mapper unit tests use small fixture rows.
"""

import json
import re
from pathlib import Path

import pytest

from src.utility.graph_api_models import Edge, GraphResponse, Node
from src.utility.typedb_graph import (
    EntityRow,
    IdRegistry,
    RelationRow,
    RolePlayer,
    build_graph,
    select_subgraph,
    validate_graph,
)


PAYLOAD_PATH = (
    Path(__file__).resolve().parents[1] / "src" / "knowledge-graph" / "example-data.json"
)


@pytest.fixture(scope="module")
def payload() -> GraphResponse:
    with PAYLOAD_PATH.open(encoding="utf-8") as handle:
        return GraphResponse.model_validate(json.load(handle))


def test_payload_has_realistic_size(payload: GraphResponse) -> None:
    assert len(payload.nodes) >= 250
    assert len(payload.edges) >= 400


def test_payload_has_expected_node_types(payload: GraphResponse) -> None:
    types = {node.type for node in payload.nodes}
    assert len(types) >= 10
    assert "login" not in types
    assert {"paperback", "contributor", "order", "review"} <= types
    assert {"publishing", "delivery"} <= types


def test_node_one_is_the_seed(payload: GraphResponse) -> None:
    seed = next(node for node in payload.nodes if node.id == 1)
    assert seed.type in {"hardback", "paperback", "ebook"}
    assert seed.title


def test_ids_and_endpoints_are_consistent(payload: GraphResponse) -> None:
    node_ids = [node.id for node in payload.nodes]
    assert len(node_ids) == len(set(node_ids))

    edge_ids = [edge.id for edge in payload.edges]
    assert len(edge_ids) == len(set(edge_ids))

    known = set(node_ids)
    for edge in payload.edges:
        assert edge.source_id in known
        assert edge.target_id in known
        assert edge.labelToTarget
        assert edge.labelToSource
        assert edge.type != "unknown"


def test_relation_nodes_have_human_labels(payload: GraphResponse) -> None:
    relation_nodes = [
        node for node in payload.nodes if node.type in {"publishing", "delivery"}
    ]
    assert relation_nodes
    for node in relation_nodes:
        assert not re.fullmatch(r"(publishing|delivery) [0-9a-f]{4}", node.title)
        assert "·" in node.title


def test_books_show_author_and_related_data(payload: GraphResponse) -> None:
    books = [
        node
        for node in payload.nodes
        if node.type in {"hardback", "paperback", "ebook"}
    ]
    assert books
    with_authors = [node for node in books if node.attributes.get("authors")]
    assert with_authors
    for node in with_authors:
        assert " — " in node.title
        assert node.attributes["authors"][0] in node.title


def test_ids_are_not_bare_short_ids(payload: GraphResponse) -> None:
    for node in payload.nodes:
        if node.type == "publication":
            assert node.title.startswith("Publication ")
        if node.type in {"order", "review"}:
            assert " · " in node.title


def test_validate_graph_accepts_export(payload: GraphResponse) -> None:
    assert validate_graph(payload) == []


def test_validate_graph_reports_missing_endpoint() -> None:
    payload = GraphResponse(
        nodes=[Node(id=1, type="book", title="seed")],
        edges=[
            Edge(
                id=1,
                source_id=1,
                target_id=99,
                labelToSource="x",
                labelToTarget="y",
                type="authoring",
            )
        ],
    )
    problems = validate_graph(payload)
    assert any("missing target" in problem for problem in problems)


def _fixture_rows() -> tuple[list[EntityRow], list[RelationRow]]:
    entities = [
        EntityRow("0x01", "paperback", {"title": "A Book"}),
        EntityRow("0x02", "contributor", {"name": "An Author"}),
        EntityRow("0x03", "publisher", {"name": "A Publisher"}),
        EntityRow("0x04", "publication", {"year": 2001}),
        EntityRow("0x05", "login", {"success": True}),
    ]
    relations = [
        RelationRow(
            "0x10",
            "authoring",
            {
                "author": RolePlayer("0x02", "contributor"),
                "work": RolePlayer("0x01", "paperback"),
            },
        ),
        RelationRow(
            "0x11",
            "publishing",
            {
                "publisher": RolePlayer("0x03", "publisher"),
                "published": RolePlayer("0x01", "paperback"),
                "publication": RolePlayer("0x04", "publication"),
            },
        ),
        RelationRow(
            "0x12",
            "action-execution",
            {
                "executor": RolePlayer("0x02", "contributor"),
                "action": RolePlayer("0x05", "login"),
            },
        ),
    ]
    return entities, relations


def test_hidden_entities_and_dangling_edges_are_dropped() -> None:
    entities, relations = _fixture_rows()
    payload = build_graph(entities, relations)

    types = {node.type for node in payload.nodes}
    assert "login" not in types
    assert all(edge.type != "action-execution" for edge in payload.edges)


def test_three_role_relation_becomes_a_node() -> None:
    entities, relations = _fixture_rows()
    payload = build_graph(entities, relations, nary_mode="node")

    relation_nodes = [node for node in payload.nodes if node.type == "publishing"]
    assert len(relation_nodes) == 1

    star_edges = [
        edge for edge in payload.edges if edge.source_id == relation_nodes[0].id
    ]
    assert len(star_edges) == 3


def test_three_role_relation_can_be_split() -> None:
    entities, relations = _fixture_rows()
    payload = build_graph(entities, relations, nary_mode="split")

    assert all(node.type != "publishing" for node in payload.nodes)
    publishing_edges = [edge for edge in payload.edges if edge.type == "publishing"]
    assert len(publishing_edges) == 2


def test_id_registry_keeps_ids_stable() -> None:
    entities, relations = _fixture_rows()
    registry = IdRegistry()

    first = build_graph(entities, relations, id_registry=registry)
    second = build_graph(entities, relations, id_registry=registry)

    assert [node.id for node in first.nodes] == [node.id for node in second.nodes]


def test_root_is_forced_to_node_one() -> None:
    entities, relations = _fixture_rows()
    payload = build_graph(entities, relations, root_iid="0x01")

    seed = next(node for node in payload.nodes if node.id == 1)
    assert seed.type == "paperback"


def test_book_title_includes_author() -> None:
    entities, relations = _fixture_rows()
    payload = build_graph(entities, relations)

    book = next(node for node in payload.nodes if node.type == "paperback")
    assert book.title == "A Book — An Author"
    assert book.attributes["authors"] == ["An Author"]


def test_relation_node_title_uses_roleplayers() -> None:
    entities, relations = _fixture_rows()
    payload = build_graph(entities, relations)

    node = next(node for node in payload.nodes if node.type == "publishing")
    assert "A Publisher" in node.title
    assert "2001" in node.title
    assert "·" in node.title


def _chain_payload() -> GraphResponse:
    nodes = [Node(id=node_id, type="book", title=f"Book {node_id}") for node_id in range(1, 5)]
    edges = [
        Edge(
            id=edge_id,
            source_id=edge_id,
            target_id=edge_id + 1,
            labelToSource="x",
            labelToTarget="y",
            type="authoring",
        )
        for edge_id in range(1, 4)
    ]
    return GraphResponse(nodes=nodes, edges=edges)


def test_select_subgraph_keeps_focus_and_one_hop() -> None:
    subgraph = select_subgraph(_chain_payload(), focus_id=2, hops=1)

    assert subgraph.focus_node_id == 2
    assert {node.id for node in subgraph.nodes} == {1, 2, 3}
    assert {edge.id for edge in subgraph.edges} == {1, 2}


def test_select_subgraph_expands_with_hops() -> None:
    subgraph = select_subgraph(_chain_payload(), focus_id=2, hops=2)

    assert {node.id for node in subgraph.nodes} == {1, 2, 3, 4}
    assert {edge.id for edge in subgraph.edges} == {1, 2, 3}


def test_select_subgraph_rejects_unknown_focus() -> None:
    subgraph = select_subgraph(_chain_payload(), focus_id=99)

    assert subgraph.nodes == []
    assert subgraph.edges == []
    assert subgraph.error is not None
    assert "focus_not_found" in subgraph.error


def test_select_subgraph_has_no_dangling_edges(payload: GraphResponse) -> None:
    seed = next(node.id for node in payload.nodes if node.id == 1)
    subgraph = select_subgraph(payload, focus_id=seed, hops=2)

    known = {node.id for node in subgraph.nodes}
    assert seed in known
    for edge in subgraph.edges:
        assert edge.source_id in known
        assert edge.target_id in known
    assert subgraph.focus_node_id == seed
