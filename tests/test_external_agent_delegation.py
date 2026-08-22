"""EAAEF-033: external principals bind existing MCP++ profiles only."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "docs/spec/external-agent-delegation.md"

REQUIRED_PROFILES = (
    "Profile A",
    "MCP-IDL",
    "Profile B",
    "CID-native",
    "Profile C",
    "UCAN",
    "execution envelope",
    "Event DAG",
    "DurableExecutor",
)

FORBIDDEN = (
    "Profile I",
    "Profile J",
    "new MCP++ profile",
)


def _spec() -> str:
    text = SPEC.read_text(encoding="utf-8")
    assert text.strip(), "delegation spec is empty"
    return text


def test_spec_reuses_existing_profiles_only() -> None:
    text = _spec()
    lowered = text.lower()
    for needle in REQUIRED_PROFILES:
        assert needle.lower() in lowered, f"missing profile binding: {needle}"
    assert "does **not** define a new MCP++ profile" in text or "not define a new MCP++ profile" in text
    assert "backend" in lowered and "storage" in lowered
    assert "must not" in lowered


def test_spec_forbids_new_profile_and_storage_authority() -> None:
    text = _spec()
    for needle in FORBIDDEN:
        # Mention of Profile I/J only as things that must not be invented.
        if needle.startswith("Profile "):
            assert "do **not** invent" in text.lower() or "do not invent" in text.lower()
    assert "granting backend or object-store authority" in text.lower() or "backend or object-store" in text.lower()
    assert "DurableExecutor" in text
    assert "fails closed" in text.lower() or "fail closed" in text.lower()


def test_mapping_table_covers_principal_fields() -> None:
    text = _spec()
    for field in (
        "principal_id",
        "repository_id",
        "run_id",
        "exact_effects",
        "expires_at_ms",
        "autonomy_ceiling",
        "resource_ceilings",
        "disclosure_policy_id",
        "provider_policy_id",
        "nonce",
        "CapabilityDecision",
        "ExternalPrincipal@1",
    ):
        assert field in text, f"mapping missing {field}"


def test_authority_sources_cannot_grant_backend_rights() -> None:
    collapsed = " ".join(_spec().lower().split())
    for source in ("prompt", "cid", "payment", "commit", "run id", "transport"):
        assert source in collapsed
    assert "authority source" in collapsed
