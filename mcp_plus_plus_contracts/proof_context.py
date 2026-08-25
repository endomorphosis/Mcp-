"""Read-only access to the frozen MCP++ proof-context v0.1 bytes.

This module deliberately supplies no canonicalizer, validator, executor,
persistence layer, provider integration, or network behavior. It only reads
the package-owned immutable bundle and decodes the requested source bytes.
"""

from __future__ import annotations

import base64
import json
from importlib import resources
from typing import Any

PROOF_CONTEXT_VERSION = "0.1"

_BUNDLE_RESOURCE = "resources/proof-context-v0.1.json"
_BUNDLE_SCHEMA = "mcp++/proof-context-v0.1-contract-bundle@1"


def contract_bundle_bytes() -> bytes:
    """Return the installed immutable contract-bundle bytes."""

    package_root = resources.files("mcp_plus_plus_contracts")
    return package_root.joinpath(_BUNDLE_RESOURCE).read_bytes()


def _bundle_document() -> dict[str, Any]:
    document = json.loads(contract_bundle_bytes())
    if not isinstance(document, dict) or document.get("schema") != _BUNDLE_SCHEMA:
        raise ValueError("invalid MCP++ proof-context contract bundle")
    return document


def _decoded_entry(entry: object) -> bytes:
    if not isinstance(entry, dict):
        raise ValueError("invalid MCP++ proof-context resource entry")
    encoded = entry.get("base64")
    expected_size = entry.get("size")
    if not isinstance(encoded, str) or not isinstance(expected_size, int):
        raise ValueError("invalid MCP++ proof-context resource encoding")
    try:
        payload = base64.b64decode(encoded, validate=True)
    except (ValueError, TypeError) as exc:
        raise ValueError("invalid MCP++ proof-context resource encoding") from exc
    if len(payload) != expected_size:
        raise ValueError("invalid MCP++ proof-context resource size")
    return payload


def schema_names() -> tuple[str, ...]:
    """Return the frozen schema filenames in stable lexical order."""

    schemas = _bundle_document().get("schemas")
    if not isinstance(schemas, dict):
        raise ValueError("invalid MCP++ proof-context schema index")
    if not all(isinstance(name, str) for name in schemas):
        raise ValueError("invalid MCP++ proof-context schema name")
    return tuple(sorted(schemas))


def schema_bytes(name: str) -> bytes:
    """Return exact admitted bytes for one proof-context v0.1 schema."""

    schemas = _bundle_document().get("schemas")
    if not isinstance(schemas, dict) or name not in schemas:
        raise KeyError(name)
    return _decoded_entry(schemas[name])


def canonical_vectors_bytes() -> bytes:
    """Return exact admitted bytes for the proof-context v0.1 vectors."""

    return _decoded_entry(_bundle_document().get("canonical_vectors"))
