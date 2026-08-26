from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas/state/state-ref-1.schema.json"
SPEC_PATH = ROOT / "docs/spec/state-ref.md"
ADR_PATH = ROOT / "docs/architecture/decisions/0004-state-modes.md"
STATE_MODEL_PATH = ROOT / "docs/architecture/state-model.md"
CLOSED_MODES = (
    "immutable",
    "single_authority",
    "causal",
    "crdt",
    "consensus",
)
WIRE_MARKER = "mcp++/state/state-ref@1"
SCHEMA_SHA256 = "377366720efed58da01fa03a1d54c7dbe0c713ee892405d0908d2dda5d984c75"


def _schema() -> dict:
    payload = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_state_ref_wire_schema_is_unchanged() -> None:
    schema = _schema()
    assert schema["properties"]["schema"]["const"] == WIRE_MARKER
    assert schema["$defs"]["consistencyMode"]["enum"] == list(CLOSED_MODES)
    assert "mode" in schema["required"]
    assert hashlib.sha256(SCHEMA_PATH.read_bytes()).hexdigest() == SCHEMA_SHA256


def test_state_docs_state_duckdb_quack_ducklake_roles_without_new_wire_fields() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    adr = ADR_PATH.read_text(encoding="utf-8")
    model = STATE_MODEL_PATH.read_text(encoding="utf-8")
    for text in (spec, adr, model):
        assert "DuckDB" in text
        assert "Quack" in text
        assert "DuckLake" in text
        assert "non-authoritative" in text or "not mutable authority" in text.lower()
        assert "transactional" in text.lower() or "CAS" in text
        assert WIRE_MARKER in text or "StateRef@1" in text
    assert "sole" in adr.lower() or "only process permitted to open" in adr
    assert "exactly one admitted, fenced, authenticated Quack" in spec
    schema = _schema()
    assert set(schema["$defs"]["consistencyMode"]["enum"]) == set(CLOSED_MODES)
    assert "ducklake" not in json.dumps(schema).lower()
