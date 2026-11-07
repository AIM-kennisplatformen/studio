"""Map TypeDB read rows onto the FCose graph payload.

POC(fcose): this module is the shared mapping layer for the bookstore mock
export and the future read-only FastMCP server. It must stay free of network
and filesystem access so both callers produce the same payload.

Inputs are already-fetched instance rows (iid, type, attributes). Output is a
``GraphResponse`` with integer node ids, which is the contract the frontend
consumes from ``GET /api/graph``.
"""

from dataclasses import dataclass, field
from typing import Iterable

from src.utility.graph_api_models import Edge, GraphResponse, Node

# Concrete bookstore entity types. ``login`` is intentionally absent; see
# HIDDEN_ENTITY_TYPES below.
ENTITY_TYPES: tuple[str, ...] = (
    "hardback",
    "paperback",
    "ebook",
    "contributor",
    "publisher",
    "courier",
    "publication",
    "user",
    "order",
    "promotion",
    "review",
    "address",
    "city",
    "state",
    "country",
)

BOOK_ENTITY_TYPES = frozenset({"hardback", "paperback", "ebook"})

# POC(fcose): logins have no useful title and only add noise to the graph.
HIDDEN_ENTITY_TYPES = frozenset({"login"})

TITLE_ATTRIBUTES: dict[str, str] = {
    "hardback": "title",
    "paperback": "title",
    "ebook": "title",
    "contributor": "name",
    "publisher": "name",
    "courier": "name",
    "publication": "year",
    "user": "name",
    "order": "id",
    "promotion": "name",
    "review": "id",
    "address": "street",
    "city": "name",
    "state": "name",
    "country": "name",
}

# Relations that name a book's author, and the role that holds the author.
AUTHOR_ROLES: dict[str, str] = {
    "authoring": "author",
    "contribution": "contributor",
}


@dataclass(frozen=True)
class RelationSpec:
    """How one TypeDB relation becomes nodes and edges.

    Binary relations get a directed edge from ``source_role`` to
    ``target_role``. Relations listed in ``THREE_PLUS_ROLES`` have more than
    two roleplayers and are handled by the n-ary policy.
    """

    name: str
    roles: tuple[str, ...]
    source_role: str | None = None
    target_role: str | None = None
    forward_label: str = ""
    backward_label: str = ""


# POC(fcose): directions and labels chosen for the bookstore schema. Roles not
# present here are rejected rather than guessed.
RELATION_SPECS: dict[str, RelationSpec] = {
    "contribution": RelationSpec(
        "contribution",
        ("contributor", "work"),
        "contributor",
        "work",
        "contributed to",
        "has contributor",
    ),
    "authoring": RelationSpec(
        "authoring",
        ("author", "work"),
        "author",
        "work",
        "authored",
        "written by",
    ),
    "editing": RelationSpec(
        "editing",
        ("editor", "work"),
        "editor",
        "work",
        "edited",
        "edited by",
    ),
    "illustrating": RelationSpec(
        "illustrating",
        ("illustrator", "work"),
        "illustrator",
        "work",
        "illustrated",
        "illustrated by",
    ),
    "promotion-inclusion": RelationSpec(
        "promotion-inclusion",
        ("promotion", "item"),
        "promotion",
        "item",
        "applies to",
        "promoted by",
    ),
    "order-line": RelationSpec(
        "order-line",
        ("order", "item"),
        "order",
        "item",
        "contains",
        "in order",
    ),
    "rating": RelationSpec(
        "rating",
        ("review", "rated"),
        "review",
        "rated",
        "rates",
        "rated by",
    ),
    "action-execution": RelationSpec(
        "action-execution",
        ("executor", "action"),
        "executor",
        "action",
        "performed",
        "performed by",
    ),
    "locating": RelationSpec(
        "locating",
        ("located", "location"),
        "located",
        "location",
        "located in",
        "contains",
    ),
    "recommendation": RelationSpec(
        "recommendation",
        ("recommended", "recipient"),
        "recommended",
        "recipient",
        "recommended to",
        "recommended by",
    ),
    # Three roleplayers: relation node by default, see build_graph(nary_mode).
    "publishing": RelationSpec(
        "publishing",
        ("publisher", "published", "publication"),
    ),
    "delivery": RelationSpec(
        "delivery",
        ("deliverer", "delivered", "destination"),
    ),
}

NARY_RELATION_TYPES = frozenset(
    name for name, spec in RELATION_SPECS.items() if len(spec.roles) > 2
)

NARY_MODES = ("node", "split", "clique")


@dataclass
class RolePlayer:
    """One roleplayer of a fetched relation instance."""

    iid: str
    type: str


@dataclass
class EntityRow:
    """One fetched entity instance."""

    iid: str
    type: str
    attributes: dict = field(default_factory=dict)


@dataclass
class RelationRow:
    """One fetched relation instance."""

    iid: str
    type: str
    roleplayers: dict[str, RolePlayer] = field(default_factory=dict)
    attributes: dict = field(default_factory=dict)


class IdRegistry:
    """Stable TypeDB iid to integer id mapping.

    POC(fcose): the mock export uses a fresh registry. The FastMCP server will
    keep one registry per user graph context so node ids stay stable across
    chat turns.
    """

    def __init__(self) -> None:
        self._ids: dict[str, int] = {}
        self._next = 1

    def get(self, key: str) -> int:
        existing = self._ids.get(key)
        if existing is not None:
            return existing
        assigned = self._next
        self._next += 1
        self._ids[key] = assigned
        return assigned

    def reserve(self, key: str, node_id: int) -> int:
        """Pin a key to an id, for example the seed node to id 1."""
        existing = self._ids.get(key)
        if existing == node_id:
            return node_id
        if existing is not None:
            return existing
        if node_id in self._ids.values():
            raise ValueError(f"node id {node_id} already assigned")
        self._ids[key] = node_id
        self._next = max(self._next, node_id + 1)
        return node_id

    def as_dict(self) -> dict[str, int]:
        return dict(self._ids)


def entity_key(iid: str) -> str:
    return f"entity:{iid}"


def relation_node_key(relation_type: str, iid: str) -> str:
    return f"relation:{relation_type}:{iid}"


def pick_root(
    entities: Iterable[EntityRow], relations: Iterable[RelationRow]
) -> str | None:
    """Pick the most connected book as the initial centre node.

    The frontend opens on node id 1, so the seed should have a useful
    neighbourhood. Ties break on the lowest iid for reproducibility.
    """
    degrees: dict[str, int] = {}
    for relation in relations:
        for roleplayer in relation.roleplayers.values():
            degrees[roleplayer.iid] = degrees.get(roleplayer.iid, 0) + 1

    candidates = [entity for entity in entities if entity.type in BOOK_ENTITY_TYPES]
    if not candidates:
        return None
    candidates.sort(key=lambda entity: (-degrees.get(entity.iid, 0), entity.iid))
    return candidates[0].iid


def build_graph(
    entities: Iterable[EntityRow],
    relations: Iterable[RelationRow],
    *,
    nary_mode: str = "node",
    root_iid: str | None = None,
    id_registry: IdRegistry | None = None,
) -> GraphResponse:
    """Build a complete ``GraphResponse`` from fetched rows."""
    if nary_mode not in NARY_MODES:
        raise ValueError(f"nary_mode must be one of {NARY_MODES}, got {nary_mode!r}")

    registry = id_registry or IdRegistry()
    entity_rows = list(entities)
    relation_rows = list(relations)
    visible = [
        entity for entity in entity_rows if entity.type not in HIDDEN_ENTITY_TYPES
    ]
    by_iid = {entity.iid: entity for entity in visible}

    root = root_iid if root_iid in by_iid else pick_root(visible, relation_rows)
    if root is not None:
        registry.reserve(entity_key(root), 1)

    authors_by_work = _authors_by_work(relation_rows, by_iid)
    titles = {
        entity.iid: _entity_title(entity, authors_by_work.get(entity.iid, ()))
        for entity in visible
    }

    nodes: list[Node] = []
    for entity in sorted(visible, key=lambda row: (row.type, titles[row.iid], row.iid)):
        attributes = dict(entity.attributes)
        if entity.iid in authors_by_work:
            attributes["authors"] = list(authors_by_work[entity.iid])
        nodes.append(
            Node(
                id=registry.get(entity_key(entity.iid)),
                type=entity.type,
                title=titles[entity.iid],
                attributes=attributes,
            )
        )

    edges: list[Edge] = []
    next_edge_id = 1

    for relation in sorted(relation_rows, key=lambda row: row.iid):
        spec = RELATION_SPECS.get(relation.type)
        if spec is None:
            raise ValueError(f"no relation spec for {relation.type!r}")

        players: list[tuple[str, EntityRow]] = []
        for role in spec.roles:
            roleplayer = relation.roleplayers.get(role)
            if roleplayer is None:
                continue
            entity = by_iid.get(roleplayer.iid)
            if entity is not None:
                players.append((role, entity))

        if len(players) < 2:
            continue

        if relation.type in NARY_RELATION_TYPES and nary_mode == "node":
            node_id = registry.get(relation_node_key(relation.type, relation.iid))
            nodes.append(
                Node(
                    id=node_id,
                    type=relation.type,
                    title=_relation_title(relation, players),
                    attributes=dict(relation.attributes),
                )
            )
            for role, entity in players:
                edges.append(
                    _edge(
                        next_edge_id,
                        node_id,
                        registry.get(entity_key(entity.iid)),
                        relation.type,
                        relation.attributes,
                        label_to_target=role,
                        label_to_source=relation.type,
                    )
                )
                next_edge_id += 1
            continue

        if relation.type in NARY_RELATION_TYPES:
            for source, target, label in _expand_nary(players, nary_mode):
                if source.iid == target.iid:
                    continue
                edges.append(
                    _edge(
                        next_edge_id,
                        registry.get(entity_key(source.iid)),
                        registry.get(entity_key(target.iid)),
                        relation.type,
                        relation.attributes,
                        label_to_target=label,
                        label_to_source=relation.type,
                    )
                )
                next_edge_id += 1
            continue

        source_role, target_role = spec.source_role, spec.target_role
        if source_role is None or target_role is None:
            raise ValueError(f"binary relation {relation.type!r} has no roles")
        source = (
            by_iid.get(relation.roleplayers[source_role].iid)
            if source_role in relation.roleplayers
            else None
        )
        target = (
            by_iid.get(relation.roleplayers[target_role].iid)
            if target_role in relation.roleplayers
            else None
        )
        if source is None or target is None or source.iid == target.iid:
            continue
        edges.append(
            _edge(
                next_edge_id,
                registry.get(entity_key(source.iid)),
                registry.get(entity_key(target.iid)),
                relation.type,
                relation.attributes,
                label_to_target=spec.forward_label,
                label_to_source=spec.backward_label,
            )
        )
        next_edge_id += 1

    return GraphResponse(nodes=nodes, edges=edges)


def _expand_nary(
    players: list[tuple[str, EntityRow]], mode: str
) -> list[tuple[EntityRow, EntityRow, str]]:
    """Reduce a 3+ roleplayer relation to binary edges without a relation node."""
    if mode == "split":
        _, hub = players[0]
        return [(hub, entity, role) for role, entity in players[1:]]

    pairs: list[tuple[EntityRow, EntityRow, str]] = []
    for index, (source_role, source) in enumerate(players):
        for target_role, target in players[index + 1 :]:
            pairs.append((source, target, target_role))
    return pairs


def _edge(
    edge_id: int,
    source_id: int,
    target_id: int,
    relation_type: str,
    attributes: dict,
    *,
    label_to_target: str,
    label_to_source: str,
) -> Edge:
    return Edge(
        id=edge_id,
        source_id=source_id,
        target_id=target_id,
        labelToSource=label_to_source,
        labelToTarget=label_to_target,
        type=relation_type,
        attributes=dict(attributes),
    )


def _authors_by_work(
    relations: Iterable[RelationRow], by_iid: dict[str, EntityRow]
) -> dict[str, list[str]]:
    """Collect author names per book from authoring and contribution relations.

    Sorted by relation iid so the order is reproducible across exports.
    """
    authors: dict[str, list[str]] = {}
    for relation in sorted(relations, key=lambda row: row.iid):
        role = AUTHOR_ROLES.get(relation.type)
        if role is None:
            continue
        author_player = relation.roleplayers.get(role)
        work_player = relation.roleplayers.get("work")
        if author_player is None or work_player is None:
            continue
        author = by_iid.get(author_player.iid)
        work = by_iid.get(work_player.iid)
        if author is None or work is None:
            continue
        name = _entity_title(author)
        names = authors.setdefault(work.iid, [])
        if name not in names:
            names.append(name)
    return authors


def _entity_title(entity: EntityRow, authors: Iterable[str] = ()) -> str:
    """Human-readable node label.

    Books get ``Title — Author`` when an author relation was found. Entity
    types whose title attribute is not self-explanatory get a short prefix.
    """
    attribute = TITLE_ATTRIBUTES.get(entity.type)
    base = None
    if attribute is not None:
        value = entity.attributes.get(attribute)
        if isinstance(value, list):
            value = value[0] if value else None
        if value not in (None, ""):
            base = str(value)
    if base is None:
        return f"{entity.type} {_short_iid(entity.iid)}"

    if entity.type == "publication":
        return f"Publication {base}"
    if entity.type == "order":
        status = entity.attributes.get("status")
        return f"{base} · {status}" if status else base
    if entity.type == "review":
        score = entity.attributes.get("score")
        return f"{base} · score {score}" if score is not None else base

    author_list = list(authors)
    if entity.type in BOOK_ENTITY_TYPES and author_list:
        if len(author_list) == 1:
            return f"{base} — {author_list[0]}"
        return f"{base} — {author_list[0]} et al."
    return base


def _relation_title(
    relation: RelationRow, players: list[tuple[str, EntityRow]]
) -> str:
    """Meaningful label for a relation node.

    Uses the roleplayer names, since relation instances in the bookstore
    schema carry no attributes of their own.
    """
    by_role = dict(players)
    if relation.type == "publishing":
        parts: list[str] = []
        publisher = by_role.get("publisher")
        publication = by_role.get("publication")
        if publisher is not None:
            parts.append(_entity_title(publisher))
        if publication is not None:
            year = publication.attributes.get("year")
            parts.append(str(year) if year is not None else _entity_title(publication))
        if parts:
            return "Publishing · " + " · ".join(parts)
    if relation.type == "delivery":
        parts = []
        courier = by_role.get("deliverer")
        destination = by_role.get("destination")
        if courier is not None:
            parts.append(_entity_title(courier))
        if destination is not None:
            parts.append(_entity_title(destination))
        if parts:
            return "Delivery · " + " to ".join(parts)

    if players:
        return f"{relation.type} · " + " · ".join(
            _entity_title(entity) for _, entity in players
        )
    return f"{relation.type} {_short_iid(relation.iid)}"


def _short_iid(iid: str) -> str:
    return iid[-4:] if len(iid) > 4 else iid


def select_subgraph(
    payload: GraphResponse, focus_id: int, hops: int = 1
) -> GraphResponse:
    """Return the subgraph within ``hops`` edges of ``focus_id``.

    POC(fcose): this is the manual stand-in for the read-only MCP server. The
    server chooses the nodes and the frontend renders exactly this payload.
    Node and edge ids are preserved so ids stay stable across focus changes.
    """
    if hops < 0:
        raise ValueError("hops must be non-negative")

    known = {node.id for node in payload.nodes}
    if focus_id not in known:
        return GraphResponse(error=f"focus_not_found: {focus_id}")

    adjacency: dict[int, set[int]] = {}
    for edge in payload.edges:
        adjacency.setdefault(edge.source_id, set()).add(edge.target_id)
        adjacency.setdefault(edge.target_id, set()).add(edge.source_id)

    selected = {focus_id}
    frontier = {focus_id}
    for _ in range(hops):
        neighbours: set[int] = set()
        for node_id in frontier:
            neighbours.update(adjacency.get(node_id, ()))
        neighbours -= selected
        if not neighbours:
            break
        selected |= neighbours
        frontier = neighbours

    nodes = [node for node in payload.nodes if node.id in selected]
    edges = [
        edge
        for edge in payload.edges
        if edge.source_id in selected and edge.target_id in selected
    ]
    return GraphResponse(nodes=nodes, edges=edges, focus_node_id=focus_id)


def validate_graph(payload: GraphResponse) -> list[str]:
    """Return human-readable contract violations, empty when valid."""
    problems: list[str] = []
    node_ids = [node.id for node in payload.nodes]
    if len(node_ids) != len(set(node_ids)):
        problems.append("duplicate node ids")
    if 1 not in set(node_ids):
        problems.append("node id 1 is missing")
    known = set(node_ids)
    for edge in payload.edges:
        if edge.source_id not in known:
            problems.append(f"edge {edge.id} has missing source {edge.source_id}")
        if edge.target_id not in known:
            problems.append(f"edge {edge.id} has missing target {edge.target_id}")
        if not edge.labelToTarget:
            problems.append(f"edge {edge.id} has no labelToTarget")
    return problems
