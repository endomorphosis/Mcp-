from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas/durable/durable-executor-1.schema.json"
ADR_PATH = ROOT / "docs/architecture/decisions/0005-durable-executor.md"
GUIDE_PATH = ROOT / "docs/architecture/durable-execution.md"
METHODS = (
    "start",
    "resume",
    "signal",
    "cancel",
    "checkpoint",
    "retry",
    "timer",
    "compensation",
    "inspect",
    "recover",
    "finalize",
)
REQUEST_MARKER = "mcp++/durable/executor-request@1"
SCHEMA_SHA256 = "d09afac45301a94b987ef6c7ace83fe5b78e8ba39877a730229785fbf626541e"


def _schema() -> dict:
    payload = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_durable_executor_wire_schema_is_unchanged() -> None:
    schema = _schema()
    encoded = json.dumps(schema)
    assert REQUEST_MARKER in encoded
    assert "DurableExecutor@1" in schema["title"] or "DurableExecutor@1" in schema["description"]
    method_enum = schema["$defs"]["methodName"]["enum"]
    for method in METHODS:
        assert method in method_enum
    assert hashlib.sha256(SCHEMA_PATH.read_bytes()).hexdigest() == SCHEMA_SHA256


def test_durable_docs_state_duckdb_journal_quack_owner_and_nonauthoritative_ducklake() -> None:
    adr = ADR_PATH.read_text(encoding="utf-8")
    guide = GUIDE_PATH.read_text(encoding="utf-8")
    for text in (adr, guide):
        assert "DuckDB" in text
        assert "Quack" in text
        assert "DuckLake" in text
        assert "journal" in text.lower()
        assert "non-authoritative" in text or (
            "never" in text.lower() and "authority" in text.lower()
        )
        assert "DurableExecutor@1" in text
    assert "one fenced, authenticated Quack owner/service" in adr
    collapsed_guide = " ".join(guide.split())
    assert "only process permitted to open the authoritative DuckDB file" in collapsed_guide
    assert "SQLite is an explicit fallback" in adr or "SQLite is an explicit fallback" in guide
    schema = _schema()
    encoded = json.dumps(schema)
    assert "restated" not in encoded
    assert REQUEST_MARKER in encoded
