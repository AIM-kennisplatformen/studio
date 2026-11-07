"""Export the TypeDB bookstore sample as the FCose mock graph payload.

POC(fcose): this is a development snapshot tool, not application runtime code.
It produces ``backend/src/knowledge-graph/example-data.json`` so the existing
graph UI can be evaluated against a realistic TypeDB dataset.

The intended production path is the read-only FastMCP server, which will reuse
``TypedbReadClient`` and ``build_graph`` from the same modules and return the same
``GraphResponse`` payload. When that server lands, this script can stay as a
regeneration tool or be deleted.

Run with the backend environment (it needs pydantic from the project):

    .pixi/envs/default/bin/python scripts/export_bookstore_graph.py \
        --out src/knowledge-graph/example-data.json --pretty
"""

import argparse
import json
import sys
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from src.utility.typedb_client import TypeDBConfig, TypeDBReadClient  # noqa: E402
from src.utility.typedb_graph import (  # noqa: E402
    ENTITY_TYPES,
    NARY_MODES,
    RELATION_SPECS,
    EntityRow,
    RelationRow,
    RolePlayer,
    build_graph,
    validate_graph,
)


DEFAULT_OUTPUT = BACKEND_ROOT / "src" / "knowledge-graph" / "example-data.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Output JSON path (default: %(default)s)",
    )
    parser.add_argument(
        "--nary",
        choices=NARY_MODES,
        default="node",
        help="How to render 3+ roleplayer relations (default: %(default)s)",
    )
    parser.add_argument(
        "--root-iid",
        default=None,
        help="Force a specific book iid to become node id 1",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Indent the output JSON",
    )
    return parser.parse_args()


def entity_query(entity_type: str) -> str:
    return (
        "match\n"
        f"  $x isa! {entity_type};\n"
        "fetch {\n"
        '  "iid": iid($x),\n'
        '  "doc": { $x.* }\n'
        "};"
    )


def relation_query(relation_type: str) -> str:
    """Build a fetch query that returns roleplayer iids and exact types."""
    spec = RELATION_SPECS[relation_type]
    variables = [f"$p{index}" for index in range(len(spec.roles))]
    type_variables = [f"$t{index}" for index in range(len(spec.roles))]
    links = ", ".join(
        f"{role}: {variable}" for role, variable in zip(spec.roles, variables)
    )
    constraints = "\n  ".join(
        f"{variable} isa! {type_variable};"
        for variable, type_variable in zip(variables, type_variables)
    )
    fields = [
        '  "iid": iid($r),',
        '  "doc": { $r.* },',
    ]
    for index, (variable, type_variable) in enumerate(zip(variables, type_variables)):
        fields.append(f'  "p{index}": iid({variable}),')
        fields.append(f'  "t{index}": label({type_variable}),')
    return (
        "match\n"
        f"  $r isa! {relation_type}, links ({links});\n"
        f"  {constraints}\n"
        "fetch {\n"
        + "\n".join(fields)
        + "\n};"
    )


def fetch_entities(client: TypeDBReadClient) -> list[EntityRow]:
    entities: list[EntityRow] = []
    for entity_type in ENTITY_TYPES:
        documents = client.fetch_documents(entity_query(entity_type))
        for document in documents:
            entities.append(
                EntityRow(
                    iid=document["iid"],
                    type=entity_type,
                    attributes=document.get("doc") or {},
                )
            )
        print(f"  {entity_type}: {len(documents)}")
    return entities


def fetch_relations(client: TypeDBReadClient) -> list[RelationRow]:
    relations: list[RelationRow] = []
    for relation_type, spec in RELATION_SPECS.items():
        documents = client.fetch_documents(relation_query(relation_type))
        for document in documents:
            roleplayers = {}
            for index, role in enumerate(spec.roles):
                roleplayers[role] = RolePlayer(
                    iid=document[f"p{index}"],
                    type=document[f"t{index}"],
                )
            relations.append(
                RelationRow(
                    iid=document["iid"],
                    type=relation_type,
                    roleplayers=roleplayers,
                    attributes=document.get("doc") or {},
                )
            )
        print(f"  {relation_type}: {len(documents)}")
    return relations


def main() -> int:
    args = parse_args()
    client = TypeDBReadClient(TypeDBConfig.from_env())
    config = client.config

    print(f"TypeDB: {config.url} database={config.database}")
    client.signin()

    print("Fetching entities")
    entities = fetch_entities(client)
    print("Fetching relations")
    relations = fetch_relations(client)

    payload = build_graph(
        entities,
        relations,
        nary_mode=args.nary,
        root_iid=args.root_iid,
    )
    problems = validate_graph(payload)
    if problems:
        for problem in problems:
            print(f"ERROR: {problem}", file=sys.stderr)
        return 1

    root = next((node for node in payload.nodes if node.id == 1), None)
    print(
        f"Wrote {len(payload.nodes)} nodes, {len(payload.edges)} edges; "
        f"root={root.title if root else None!r}"
    )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as handle:
        json.dump(
            payload.model_dump(mode="json"),
            handle,
            indent=2 if args.pretty else None,
        )
        handle.write("\n")
    print(f"Output: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
