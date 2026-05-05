# Connector Framework Reference

This document is the engineering reference for the connector layer at `src/connectors/`. It covers the abstractions, conventions, and patterns used to build connectors that pull compliance evidence from customer systems.

For the product thesis behind this layer — why sovereign collection, why capability-gap detection, why continuous validation — see `docs/CONNECTOR_LAYER.md`. This document assumes that context and focuses on the engineering specifics.

## Layout

```
src/connectors/
├── __init__.py              # Eager imports — gates connector visibility
├── base.py                  # BaseConnector ABC, PulledEvidence dataclass
├── registry.py              # @register decorator, list_types(), get_connector_class()
├── runner.py                # Sync runner orchestrator + persistence
├── crypto.py                # Fernet credential encryption
├── connectors_builtin/
│   ├── echo.py              # Plumbing-verification connector
│   ├── entra_id.py          # Microsoft Entra ID (Phase 5.2)
│   └── m365_gcc_high.py     # M365 + Purview + audit-log (Phase 5.3)
└── _msgraph/                # Microsoft Graph helper layer (reusable)
    ├── auth.py              # MSAL token manager, per-cloud authority
    ├── client.py            # Sync HTTP client, paginate(), post_for_async()
    ├── endpoints.py         # CloudEnvironment enum, base URL routing
    ├── retry.py             # get_with_retry, capability-gap detectors
    ├── async_query.py       # post_for_async + poll_until_done helpers
    └── errors.py            # Exception taxonomy
```

## Core abstractions

### BaseConnector

Every connector inherits from `BaseConnector` (defined in `base.py`) and implements five methods:

```python
class BaseConnector(ABC):
    type_name: str = "..."                  # unique identifier; lowercase snake_case
    supported_controls: list[str] = [...]   # NIST 800-171 control IDs

    @classmethod
    @abstractmethod
    def credentials_schema(cls) -> list[dict]:
        """Typed field definitions for the setup wizard.

        Each field is a dict with keys: name, type, label, required.
        Type is one of: text, password, select, textarea.
        Select fields also include options: list[dict] with value/label.
        """

    @classmethod
    def setup_component(cls) -> str | None:
        """Optional escape-hatch component name.

        Return None for connectors that fit the four-field-type schema
        (almost all of them). Return a string identifying a custom React
        component if the connector needs configuration that doesn't fit.
        """
        return None

    @abstractmethod
    def test_connection(self) -> dict:
        """Validate credentials are usable. Called before pull().

        Returns dict with keys: status ("ok" | "failed"), message (str).
        Should be cheap — single API call, narrow permission scope.
        """

    @abstractmethod
    def pull(self) -> Iterator[PulledEvidence]:
        """Yield evidence for each supported control.

        Per-control exceptions are caught by the orchestrator and
        accumulated via get_pull_errors(). Don't catch and swallow
        broad exceptions inside pull() — let the orchestrator isolate
        per-control failures.
        """

    def get_pull_errors(self) -> list[str]:
        """Errors accumulated during the most recent pull(), formatted
        as pipe-delimited strings via format_pull_error()."""
```

The `setup_component` escape hatch exists for connectors whose configuration doesn't fit the four-field-type schema. It hasn't been used yet; Sentinel may be the first user (workspace_id / subscription_id / region cascade).

### PulledEvidence

Returned by `pull()`. Defined in `base.py`. Fields:

| Field | Type | Default | Purpose |
|---|---|---|---|
| `filename` | `str` | required | Used for evidence artifact storage |
| `content` | `str` | required | JSON-serialized evidence body |
| `control_ids` | `list[str]` | required | NIST 800-171 control IDs supported by this evidence |
| `metadata` | `dict` | required | Free-form metadata (endpoints, counts, timestamps, status keys) |
| `coverage_scope` | `Literal["full", "partial"]` | `"full"` | Source completeness |
| `missing_sources` | `list[str]` | `[]` | Free-form list when partial |
| `evidence_directness` | `Literal["raw_config", "aggregate"]` | `"raw_config"` | Raw config vs Microsoft-derived score |
| `degraded` | `bool` | `False` | Sub-component unavailable; emit degraded rather than fail |
| `degradation_reason` | `str \| None` | `None` | Free-form when degraded |

The five optional fields were added in F.1 as framework contracts. They default-respect — connectors written before F.1 (`EntraIdConnector`) work unchanged, and the SSP narrative pipeline reads them when present to render degradation explicitly rather than fabricate coverage claims.

`PulledEvidence` deliberately has no `source` field. Cross-connector dedup uses the row-level `connector_runs.id` → `connectors.type_name` linkage on emitted `evidence_artifacts`; the metadata-level signature is `metadata["endpoints"]`. Adding a `source` field would be a framework-level amendment for cosmetic dedup signaling and would not change the actual mechanism.

### Registry

`registry.py` exposes:

- `@register` — class decorator that adds a connector to the global registry. Applied at module-import time.
- `list_types() -> list[dict]` — returns connector types currently registered. Reads `_REGISTRY` directly.
- `get_connector_class(type_name: str) -> Type[BaseConnector]` — looks up a connector class by `type_name`.

The visibility gate is in `src/connectors/__init__.py`: a connector is visible to `list_types()` only if `__init__.py` eager-imports it. Connectors registered via `@register` but not eager-imported will load when something imports them directly, but won't appear on `/api/connectors/types` until the eager-import is added.

This separation enables the **invisibility-then-flip** discipline (see Conventions below).

## The MsGraph helper layer

`src/connectors/_msgraph/` is the reusable foundation under every Microsoft Graph connector. Future Microsoft connectors should depend on it rather than rolling their own HTTP client, auth, or error handling. Non-Microsoft connectors (CrowdStrike, etc.) will have their own helper layers structured analogously.

### Cloud routing

`endpoints.py` defines:

```python
class CloudEnvironment(str, Enum):
    COMMERCIAL = "commercial"      # graph.microsoft.com / login.microsoftonline.com
    GCC_HIGH = "gcc_high"          # graph.microsoft.us / login.microsoftonline.us
    DOD = "dod"                    # dod-graph.microsoft.us / login.microsoftonline.us
```

Every connector that talks to Microsoft Graph takes `cloud_environment` as a credential field (a `select` with three options). `MsGraphClient` constructs URLs through `_build_url()`, which routes by cloud and adds the `/v1.0/` or `/beta/` prefix automatically based on the path passed in.

**Never construct Graph URLs by hand.** All URL construction goes through `endpoints.py` so the cloud-routing layer is the single source of truth. The static-source-lint check planned for F.5 will flag any literal `graph.microsoft.com` / `graph.microsoft.us` / `login.microsoftonline.com` / `login.microsoftonline.us` / `.default` outside `_msgraph/endpoints.py` and `_msgraph/auth.py`.

### Sync HTTP client

`MsGraphClient` (in `client.py`) is a sync `httpx.Client` wrapper with:

- Per-cloud token caching via `TokenManager` (MSAL-backed, `ConfidentialClientApplication`)
- `paginate(path, max_pages=100) -> Iterator[dict]` — yields flat items, follows `@odata.nextLink`
- `post_for_async(path, body) -> dict` — POST to async-query endpoints (delegates to `async_query.post_for_async`)
- `poll_until_done(query_path, *, max_wait_seconds=300, poll_interval_seconds=5) -> dict` — poll until terminal status (delegates to `async_query.poll_until_done`)
- Beta-endpoint support: paths prefixed with `/beta/` route to the beta endpoint (added F.3b)

Use `with MsGraphClient(...) as client:` for proper resource cleanup.

### Async queries

Some Microsoft Graph endpoints — notably `/beta/security/auditLog/queries` — use a POST-create-then-poll pattern. The helpers in `async_query.py` (added F.1.5) handle this:

```python
posted = client.post_for_async("/beta/security/auditLog/queries", body={
    "displayName": "Intranest AU.L2-3.3.1 audit pull 2026-05-04T00:00:00Z",
    "filterStartDateTime": "2026-05-04T00:00:00Z",
    "filterEndDateTime": "2026-05-05T00:00:00Z",
})
query_id = posted["id"]
polled = client.poll_until_done(f"/beta/security/auditLog/queries/{query_id}")
records = list(client.paginate(f"/beta/security/auditLog/queries/{query_id}/records"))
```

Three exceptions can fire from this pattern:

- `MsGraphAsyncTimeoutError` — polling exceeded `max_wait_seconds` without terminal status. `last_status` kwarg carries the last non-terminal status seen.
- `MsGraphAsyncFailureError` — Microsoft returned a terminal `failed` or `cancelled` status. `terminal_status` kwarg carries which.
- `MsGraphCapabilityError` — capability gap detected during POST or polling (see below). Same exception class as GET-path detection.

POST retries are narrower than GET retries: only `httpx.ConnectError` and 429 are retried. 5xx and `ReadTimeout` are not retried because they risk creating duplicate resources.

### Capability-gap detection

Microsoft Graph signals tenant-level service unavailability through four empirically-validated shapes. All four raise `MsGraphCapabilityError` to connector code, so consumers handle one exception class regardless of which underlying detector fired. Detector code lives in `retry.py`.

| # | Signal | Outer code | Discriminator |
|---|---|---|---|
| 1 | Licensing (403) | `Forbidden_LicensingError` | Exact code match → `_detect_licensing_signal` |
| 2 | Capability gap (400) | `BadRequest` | Fragment match in `error.message` → `_detect_capability_gap` |
| 3 | Service unavailable (500) | `generalException` | Auth-token fragment in `innerError.message` → `_detect_service_unavailable_500` |
| 4 | Audit disabled (400) | `UnknownError` | `AuditingDisabledTenant` in stringified `error.message` → `_detect_audit_disabled_400` |

GET requests run through `_classify_400_or_raise` and `_classify_500_or_continue_retry`. POST requests run through the same `_classify_400_or_raise` (extracted in F.3c so GET/POST classification is symmetric across the helper layer).

The "grow on encounter" policy: when a new signal shape appears in production, add a fifth (or sixth) narrow detector. Don't widen existing detectors to also match — they're narrow on purpose so they don't false-positive on real errors. New detectors land in `retry.py` next to the existing four, with a frozenset of fragments and a small `_detect_*_*` helper, narrow-signature, complementary to existing detectors.

## Conventions

### Closed-set status keys

Sub-component status within a single control's evidence is communicated via closed-set status keys in `metadata`. Currently in use:

| Key | Closed set | Used by |
|---|---|---|
| `intune_status` | `ok`, `license_not_detected`, `service_unavailable` | MP.L2-3.8.1 |
| `sharepoint_status` | `ok`, `service_unavailable` | MP.L2-3.8.1, MP.L2-3.8.2 |
| `secure_score_status` | `ok`, `service_unavailable` | SC.L2-3.13.8 |
| `sensitivity_label_status` | `ok`, `service_unavailable`, `license_not_detected` | AC.L2-3.1.3, SC.L2-3.13.8 |
| `audit_query_status` | `ok`, `service_unavailable`, `license_not_detected`, `timeout` | AU.L2-3.3.1 (M365) |

Plus the `media_scope: "digital"` convention on MP.L2-3.8.1 / MP.L2-3.8.2 (paper-media exclusion; future paper-media controls would set `"paper"`).

Add new status keys when a control has multiple sub-components that fail independently. Keep the value sets closed — don't add free-form status strings, since downstream pipelines (SSP narrative generation) need to enumerate the possibilities.

### Sub-pass discipline

Larger work units (a new connector, a new framework primitive) are split into sub-passes during discovery, before any code is written. Each sub-pass ships independently with its own commit, tests, and live smoke. Pass E retrofitted this; Pass F applied it from the start (F.1 / F.1.5 / F.2 / F.3a/b/c/d / F.4 / F.5).

The patterns:

- **Pre-split sub-passes during discovery, not retrofit under deadline.** Pass E learned this the hard way (E.3 retrofit into E.3a/b/c/d); Pass F applied it from the start.
- **Inline live smoke per sub-pass**, not deferred to a single end-of-pass harness. This is what catches framework-level findings the mocked-fixture tests can't see — capability-gap shapes #2, #3, and #4 were all surfaced this way.
- **Default-respect contract**: zero edits to existing test files except where explicitly authorized for evolving evidence shape. Held across all of Pass F's eight sub-passes (one explicit exception: F.3d's invisibility-test rewrite, since the tests *were* the contract being flipped).
- **Carryover-as-commit-message**: scope deferrals are named in the commit that surfaced them, with the destination phase identified. Makes deferred work auditable rather than just deferred.

### Invisibility-then-flip

Connectors ship as code-on-disk with their `@register` decorator running but their import gated. The eager-import in `src/connectors/__init__.py` is added in the *last* sub-pass before the connector goes live. This pattern serves two purposes: the connector can be developed across multiple sub-passes without exposing partial functionality on `/api/connectors/types`, and static-source-check tests provide a cheap, order-independent contract that the import gate is in the expected state.

Pattern:
- During development passes: tests assert `"<connector>" not in __init__.py source`.
- Final exposure pass: flip the import line, flip the assertion shape (this is the one authorized edit to existing tests), add an endpoint-wiring smoke test.

The `entra_id` and `m365_gcc_high` registration tests are canonical examples. New connectors should follow the same shape.

## Adding a new connector

Walkthrough using the existing `entra_id` and `m365_gcc_high` connectors as templates.

### 1. Decide the sub-pass split

Before writing code, decide the sub-passes. For a Microsoft connector, the canonical split is:

1. **Framework contracts** (only if new contracts are needed; otherwise skip).
2. **Helper layer additions** (only if a new auth flow / async pattern is needed).
3. **Connector skeleton + live `test_connection()` proof.** Connector class, `credentials_schema`, `test_connection`, `pull()` stubbed with `NotImplementedError`. Live smoke against a real tenant validates auth.
4. **Per-control pull implementations.** Split by control or by sub-component, with inline live smoke per sub-pass.
5. **Eager-import flip + endpoint-wiring smoke.** The visibility gate flips, an endpoint-wiring smoke confirms the connector is recognized.
6. **Live verification harness** (parallel to `verify_entra_id.py`).
7. **Hardening + post-mortem.**

Non-Microsoft connectors will need their own helper layer. Mirror the `_msgraph` shape: auth manager, sync client, retry/error taxonomy, capability-gap detection if applicable.

### 2. Skeleton

```python
# src/connectors/connectors_builtin/<connector>.py

from src.connectors.base import BaseConnector, PulledEvidence
from src.connectors.registry import register

@register
class MyConnector(BaseConnector):
    type_name = "my_connector"
    supported_controls = ["AC.L2-3.1.1", "..."]

    def __init__(self, *, credentials: dict):
        self._credentials = credentials
        self._pull_errors: list[str] = []

    @classmethod
    def credentials_schema(cls) -> list[dict]:
        return [
            {"name": "tenant_id", "type": "text", "label": "Tenant ID", "required": True},
            # ...
        ]

    def test_connection(self) -> dict:
        # Single cheap call to validate credentials
        ...

    def pull(self):
        for control_id in self.supported_controls:
            try:
                yield self._pull_control(control_id)
            except Exception as exc:
                self._pull_errors.append(format_pull_error(control_id, "...", exc))

    def get_pull_errors(self) -> list[str]:
        return list(self._pull_errors)
```

Don't add the connector to `src/connectors/__init__.py` yet — the invisibility contract holds during development.

### 3. Per-control implementation

Match the existing pattern in `entra_id.py` or `m365_gcc_high.py`. For Microsoft connectors, use the `_msgraph` helper layer; don't re-implement HTTP, auth, or pagination.

For controls that may hit capability gaps (any service that some tenants don't provision), wrap the pull in `try/except MsGraphCapabilityError` and emit `degraded=True` evidence with an appropriate closed-set status key in `metadata`. The pattern from `_pull_au_3_3_1`:

```python
audit_query_status = "ok"
degradation_reason = None
query_id: str | None = None
try:
    posted = client.post_for_async("/beta/security/auditLog/queries", body=...)
    query_id = posted["id"]
    polled = client.poll_until_done(f"/beta/security/auditLog/queries/{query_id}")
    records = list(client.paginate(f"/beta/security/auditLog/queries/{query_id}/records"))
except MsGraphPermissionError as exc:
    if exc.licensing_signal:
        audit_query_status = "license_not_detected"
        degradation_reason = "Audit log query license not detected on tenant"
    else:
        raise  # non-licensing 403 propagates to orchestrator
except MsGraphCapabilityError as exc:
    audit_query_status = "service_unavailable"
    degradation_reason = f"Audit log query service unavailable on tenant: {exc}"
except MsGraphAsyncTimeoutError as exc:
    audit_query_status = "timeout"
    degradation_reason = f"Audit log query timeout (last_status={exc.last_status!r})"
except MsGraphAsyncFailureError as exc:
    audit_query_status = "service_unavailable"
    degradation_reason = f"Audit log query failed (status={exc.terminal_status!r})"
```

### 4. Tests

Live in `tests/connectors/test_<connector>.py`. Conventions:

- Mock the helper-layer client with `MagicMock`, configure `client.get`, `client.paginate`, `client.post_for_async`, `client.poll_until_done` as needed.
- One test class per pulled control.
- Capability-gap tests assert all relevant signal shapes route to the appropriate degraded-evidence path.
- Cross-detector ordering tests when adding new detectors.
- A registration test file (`test_<connector>_registration.py`) asserts the invisibility-then-flip contract via static-source check.

### 5. Live verification harness

Parallel to `verify_entra_id.py` and (eventually) `verify_m365_gcc_high.py`. The harness loads credentials from `.env`, instantiates the connector, runs `test_connection`, runs `pull` against a real tenant, and writes a redacted report.

After F.4 ships, the verification harness becomes a `ConnectorVerificationHarness` base class that connector-specific scripts subclass. New connectors after that point inherit the standard report schema, PII redaction layer, and report-writer.

## Testing

### Unit tests

`tests/connectors/test_<connector>.py` for behavioral tests. Mocks the helper-layer client. Should run in <2 seconds and not make network calls.

`tests/connectors/_msgraph/` for helper-layer tests. `httpx.MockTransport(handler)` for low-level retry tests; direct calls to `post_for_async` / `poll_until_done` at the HTTP level.

`tests/connectors/test_<connector>_registration.py` for the invisibility-then-flip contract. Static-source-check pattern (read `__init__.py`, assert presence/absence of import line).

### Live smokes

Per-sub-pass live smokes against real tenants. Not in the pytest suite — they require credentials and external network access. Each connector has a `check_<connector>_auth.py` script (e.g., `check_m365_auth.py`) for one-shot validation.

The pre-commit gate is: every sub-pass that touches connector code must demonstrate live smoke against a real tenant before commit. This is what surfaces framework-level findings that mocks can't see — every capability-gap signal beyond the first was discovered this way.

## Common pitfalls

These are the things that have cost time during Pass E and Pass F. Avoid them.

- **Don't construct Graph URLs by hand.** Use `_msgraph.endpoints` for all URL construction so cloud-routing is the single source of truth.
- **Don't catch broad exceptions inside `pull()`.** Per-control exceptions are caught by the orchestrator's per-control isolator; broad exception swallowing inside the connector hides bugs.
- **Don't widen capability-gap detectors to absorb new signal shapes.** Add a new narrow detector instead. Detectors are narrow on purpose to avoid false-positives on real errors.
- **Don't add eager imports to `__init__.py` during development.** The invisibility contract is the discipline that lets connectors ship across multiple sub-passes safely.
- **Don't edit existing tests outside the explicitly-authorized scope.** The default-respect contract is what keeps Pass F-style sub-pass discipline tractable. The one exception is the invisibility-then-flip moment, where the tests *are* the contract being flipped.
- **POST retries are narrower than GET retries.** `ConnectError` + 429 only; never 5xx or `ReadTimeout`. POST retries on 5xx risk duplicate resource creation.
- **Beta endpoints are live and necessary.** `/security/auditLog/queries` is `/beta/`-only despite Microsoft's documentation suggesting otherwise. Verify against live tenants before assuming v1.0 paths exist.
- **`PulledEvidence` has no `source` field.** Cross-connector dedup uses the row-level `connector_runs.id` → `connectors.type_name` linkage on emitted `evidence_artifacts`; the metadata-level signature is `metadata["endpoints"]`.

## Existing connectors

| Connector | type_name | Controls | Cloud-aware | Phase |
|---|---|---|---|---|
| Echo | `echo` | (none — plumbing verification) | No | 5.1 |
| Entra ID | `entra_id` | AC.L2-3.1.1, IA.L2-3.5.3, AC.L2-3.1.5, AU.L2-3.3.1, AC.L2-3.1.20 | Yes | 5.2 |
| M365 GCC High | `m365_gcc_high` | MP.L2-3.8.1, MP.L2-3.8.2, AC.L2-3.1.3, SC.L2-3.13.8, AU.L2-3.3.1 | Yes | 5.3 (Pass F) |

Future:

- CrowdStrike Falcon (Pass G) — different OAuth2 flow, region picker (US-1, US-2, EU-1, US-GOV-1, US-GOV-2), Falcon-specific error envelope. First connector to introduce delta detection primitives.
- Sentinel SIEM (Pass H) — likely first user of `setup_component` escape-hatch (workspace_id / subscription_id / region cascade). Event-stream data shape, KQL queries.
- PreVeil GRC, Tenable, KnowBe4 — connector breadth, scheduled post-Pass-I on customer demand.

---

This document evolves as the framework grows. When new patterns crystallize, add them here. Source-of-truth precedence: if this document conflicts with code, the code wins, but the document gets updated in the same commit that introduces the divergence.
