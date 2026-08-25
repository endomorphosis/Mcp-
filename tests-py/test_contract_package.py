from __future__ import annotations

import ast
import base64
import hashlib
import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mcp_plus_plus_contracts import (  # noqa: E402, I001
    PROOF_CONTEXT_VERSION,
    canonical_vectors_bytes,
    contract_bundle_bytes,
    schema_bytes,
    schema_names,
)


SCHEMA_ROOT = ROOT / "schemas" / "proof-context" / "v0.1"
VECTOR_PATH = ROOT / "conformance" / "vectors" / "proof-context-v0.1.json"
PACKAGE_ROOT = ROOT / "mcp_plus_plus_contracts"

SCHEMA_COMMIT = "5a4b14439245a9c54804b3eb1d7f198e3e25e7de"
SCHEMA_TREE = "442a84f4a4c054e8d3615e9e0d70047cfc6be61c"
VECTOR_COMMIT = "85b8d03e767cd0ca7f4c8994013c27d31f03e817"
VECTOR_TREE = "0b65dff9e2ff2be513ffac32c9fcd27838de4ead"


def _raw_cid(payload: bytes) -> str:
    digest = hashlib.sha256(payload).digest()
    cid_bytes = b"\x01\x55\x12\x20" + digest
    return "b" + base64.b32encode(cid_bytes).decode("ascii").lower().rstrip("=")


def _bundle() -> dict[str, object]:
    document = json.loads(contract_bundle_bytes())
    assert isinstance(document, dict)
    return document


def test_bundle_is_exact_projection_of_frozen_schemas_and_vectors() -> None:
    bundle = _bundle()
    expected_names = tuple(path.name for path in sorted(SCHEMA_ROOT.glob("*.json")))

    assert PROOF_CONTEXT_VERSION == "0.1"
    assert bundle["schema"] == "mcp++/proof-context-v0.1-contract-bundle@1"
    assert bundle["contract_version"] == PROOF_CONTEXT_VERSION
    assert bundle["runtime_authority"] is False
    assert schema_names() == expected_names

    provenance = bundle["generated_from"]
    assert provenance == {
        "repository": "https://github.com/endomorphosis/Mcp-Plus-Plus.git",
        "schema_commit": SCHEMA_COMMIT,
        "schema_tree": SCHEMA_TREE,
        "vector_commit": VECTOR_COMMIT,
        "vector_tree": VECTOR_TREE,
    }

    entries = bundle["schemas"]
    assert isinstance(entries, dict)
    for name in expected_names:
        source = (SCHEMA_ROOT / name).read_bytes()
        packaged = schema_bytes(name)
        entry = entries[name]
        assert isinstance(entry, dict)
        assert packaged == source
        assert entry["path"] == f"schemas/proof-context/v0.1/{name}"
        assert entry["size"] == len(source)
        assert entry["sha256"] == hashlib.sha256(source).hexdigest()
        assert entry["cid"] == _raw_cid(source)

    vector_source = VECTOR_PATH.read_bytes()
    vector_entry = bundle["canonical_vectors"]
    assert isinstance(vector_entry, dict)
    assert canonical_vectors_bytes() == vector_source
    assert vector_entry["path"] == "conformance/vectors/proof-context-v0.1.json"
    assert vector_entry["size"] == len(vector_source)
    assert vector_entry["sha256"] == hashlib.sha256(vector_source).hexdigest()
    assert vector_entry["cid"] == _raw_cid(vector_source)


def test_unknown_schema_fails_closed() -> None:
    with pytest.raises(KeyError):
        schema_bytes("not-admitted.schema.json")


def test_package_has_no_runtime_or_provider_authority() -> None:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'name = "mcp-plus-plus-contracts"' in pyproject
    assert "dependencies = []" in pyproject
    assert "[project.scripts]" not in pyproject

    allowed_imports = {"__future__", "base64", "importlib", "json", "typing"}
    declarations: list[ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef] = []
    for source_path in sorted(PACKAGE_ROOT.glob("*.py")):
        tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
        imported = {
            node.names[0].name.split(".", 1)[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
        }
        imported.update(
            (node.module or "").split(".", 1)[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.level == 0
        )
        assert imported <= allowed_imports
        declarations.extend(
            node
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        )

    forbidden_names = {
        "canonicalize",
        "execute",
        "install",
        "persist",
        "provider",
        "route_model",
        "validate",
    }
    assert not {node.name for node in declarations} & forbidden_names


def test_wheel_works_without_source_tree_on_import_path(tmp_path: Path) -> None:
    dist_dir = tmp_path / "dist"
    site_dir = tmp_path / "site"
    dist_dir.mkdir()
    env = os.environ.copy()
    env["SOURCE_DATE_EPOCH"] = "0"
    env.pop("PYTHONPATH", None)

    subprocess.run(
        [
            sys.executable,
            "-m",
            "build",
            "--wheel",
            "--no-isolation",
            "--outdir",
            str(dist_dir),
            str(ROOT),
        ],
        check=True,
        cwd=tmp_path,
        env=env,
    )
    wheel = next(dist_dir.glob("mcp_plus_plus_contracts-0.1.0-*.whl"))
    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())
    assert "mcp_plus_plus_contracts/__init__.py" in names
    assert "mcp_plus_plus_contracts/proof_context.py" in names
    assert "mcp_plus_plus_contracts/resources/proof-context-v0.1.json" in names
    assert not any(name.endswith("mcpp.py") for name in names)
    assert not any(name.startswith(("cli/", "schemas/", "conformance/")) for name in names)

    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--no-deps",
            "--target",
            str(site_dir),
            str(wheel),
        ],
        check=True,
        cwd=tmp_path,
        env=env,
    )
    probe = f"""
import json
import pathlib
import sys

source_root = pathlib.Path({str(ROOT)!r})
site_root = pathlib.Path({str(site_dir)!r})
assert all(pathlib.Path(item or '.').resolve() != source_root for item in sys.path)
sys.path.insert(0, str(site_root))
import mcp_plus_plus_contracts as contracts
assert pathlib.Path(contracts.__file__).resolve().is_relative_to(site_root)
assert len(contracts.schema_names()) == 17
assert json.loads(contracts.canonical_vectors_bytes())["schema"] == "mcp++/conformance/proof-context-v0.1-vectors@1"
print(contracts.PROOF_CONTEXT_VERSION)
"""
    completed = subprocess.run(
        [sys.executable, "-I", "-c", probe],
        check=True,
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
    )
    assert completed.stdout.strip() == "0.1"
