# External-agent delegation on existing MCP++ profiles

**Status:** Normative mapping for External Agent Autonomous Execution Fabric
(EAAEF-033). This document does **not** define a new MCP++ profile.

## 1. Non-goals

- Do **not** invent Profile I, Profile J, or any other new MCP++ profile.
- Do **not** grant backend, storage, secret, proof-key, or merge authority
  from a prompt, CID, payment, commit, run ID, or transport authentication
  token.
- Do **not** treat DurableExecutor as a default runtime. Use it only where
  the admitted configuration already selects that runtime.

The external principal is an **audience and caveat binding** onto Profiles
A–C, F, the execution envelope, and existing fencing. Backend authority
remains outside the delegated surface.

## 2. Existing profiles reused

| MCP++ profile | Spec | External-agent use |
| --- | --- | --- |
| Profile A — MCP-IDL | [mcp-idl.md](mcp-idl.md) | Interface CID and method surface for handoff tools |
| Profile B — CID-native artifacts | [cid-native-artifacts.md](cid-native-artifacts.md) | Session, receipt, and ContextPack identities |
| Profile C — UCAN delegation | [ucan-delegation.md](ucan-delegation.md) | Attenuated capability chain evaluated at execution time |
| Execution envelope / runtime | [execution-envelope.md](execution-envelope.md) | Invocation wrapper; no storage grant |
| Profile F — Event DAG | [event-dag-ordering.md](event-dag-ordering.md) | Causal event lineage for handoff/status/steer |
| Fencing / DurableExecutor | [durable-execution.md](../architecture/durable-execution.md), ADR-0005 | Optional resume/checkpoint only when configured |

## 3. Mapping table

| ExternalPrincipal@1 / CapabilityDecision@1 field | Existing MCP++ binding | Authority effect |
| --- | --- | --- |
| `principal_id` (did:key) | UCAN audience | Identifies the delegated audience; does not mint storage rights |
| `repository_id` | CID-native artifact / interface scope | Binds one repository identity |
| `run_id` | Event DAG root / fence token | Binds one run; replay of another run fails closed |
| `exact_effects` | UCAN caveats + MCP-IDL methods | Closed allowlist; unknown effects fail closed |
| `expires_at_ms` | UCAN time bound | Execution-time expiry |
| `autonomy_ceiling` | Policy CID (Profile D when present) plus UCAN attenuation | Cannot self-elevate |
| `resource_ceilings` | Operational constraints on the envelope | CPU/RAM/disk/timeout only |
| `disclosure_policy_id` | Policy CID | Disclosure is not mutation authority |
| `provider_policy_id` | Envelope runtime constraint | Provider allowlist, not backend admin |
| `nonce` | Fence / generation token | One-use bind; replay fails |
| `CapabilityDecision.verdict` | Execution-time UCAN evaluation | Permit or deny; never inferred from CID/prompt/payment/commit |

## 4. Execution-time enforcement

Delegation proofs are content-addressed (`proof_cid`) under Profile C.
Evaluators **MUST** verify issuer, audience, caveats, and expiry at
invocation time. A CID, imported history, prompt, payment, commit, run ID,
or transport authentication token **MUST NOT** be treated as an authority source.
Those values may appear as evidence or correlation identifiers only.

Storage, secret, proof-key, and merge authority remain ungranted unless an
authenticated principal already carries that exact effect and an independent
approval record exists for that input binding.

## 5. Forbidden grants

The following are forbidden on this mapping:

- Creating a new MCP++ profile name for external agents.
- Granting backend or object-store authority to an external caller.
- Widening `exact_effects` from transport authentication.
- Using DurableExecutor as an implicit grant of resumable mutation.

DurableExecutor methods (`start`, `resume`, `checkpoint`, …) are admitted
only when the configured runtime profile already includes that executor.
Unconfigured DurableExecutor use fails closed.
