# The Connector Layer: What We're Building and Why

Intranest is a compliance platform for organizations that can't use compliance platforms.

The Defense Industrial Base — roughly 76,000 contractors handling Controlled Unclassified Information for the Department of Defense — needs to demonstrate compliance with NIST SP 800-171 to bid on contracts. They need to do this continuously, with evidence that satisfies a third-party assessor, on a budget that survives. The existing options for them are cloud-native multi-tenant SaaS GRC platforms (Drata, Vanta) that can't legally hold CUI, document-management tools (Totem, PreVeil GRC, FutureFeed) that don't automate evidence collection, enterprise on-prem suites (Archer, ServiceNow GRC) priced for Fortune 500 buyers, and consultants who write a $30,000 SSP that goes stale on day one. None of these works for a 45-person subcontractor that needs continuous compliance and can't put their data in someone else's cloud.

Intranest is built for that gap. The platform's wedge is the connector layer — software that runs inside the customer's network, pulls cybersecurity evidence from the systems they already use, and continuously validates compliance posture without exfiltrating regulated data. This document explains what the connector layer is, why it's the product rather than a feature, and how the architecture earns the claims being made about it.

For the engineering reference — abstractions, conventions, and patterns for adding a connector — see [`src/connectors/README.md`](../src/connectors/README.md). This document focuses on the why; that one focuses on the how.

## The problem with existing options

The compliance software market has stratified into four categories, each of which fails the DIB market in a different way.

The cloud-native GRC platforms — Drata, Vanta, Sprinto, Secureframe — have made GRC operationally tractable for the SOC 2 and ISO 27001 commercial markets through extensive integrations and continuous monitoring. They typically support 300+ third-party connectors and offer real-time dashboards. They are also multi-tenant SaaS hosted in their own clouds. For an organization handling CUI under DFARS 252.204-7012 and the forthcoming CMMC rule, sending CUI-adjacent metadata to a third-party SaaS in commercial cloud is a regulatory non-starter regardless of how good the product is. Compliance platforms that can't legally serve the customers they'd otherwise be a fit for are not really an option.

The CMMC-purpose-built tools — Totem, PreVeil GRC, FutureFeed, CMMC Dashboard — solved the regulatory positioning by being narrower. They typically run as document management, organizing controls and evidence into structured workflows, with prices in the $3,000–$15,000 per year range. They don't pull evidence from customer systems automatically, don't validate it for hashing or integrity, and don't update continuously. The customer still does the work; the tool helps organize it. For a contractor preparing for a third-party assessment, that's better than spreadsheets, but it doesn't move the needle on the actual cost of compliance — which is dominated by the engineering hours spent producing and maintaining evidence, not the documentation cost.

The enterprise on-prem suites — Archer, ServiceNow GRC, IBM OpenPages — have the deployment posture right but are priced and shaped for Fortune 500 buyers. Implementations run six figures plus consulting overhead. The 45-person defense subcontractor never enters their sales motion.

The consultant model is structurally unable to deliver continuous compliance. A consultant writes an SSP for $30,000 to $60,000 over three to six months, hands it to the contractor, and walks away. The document is accurate on the day it's signed and gradually drifts from reality as the contractor's actual systems evolve. This is the model most contractors actually use today, and it's also why most contractors are anxious about C3PAO assessment — they have an SSP, but they don't have evidence the SSP currently describes their systems.

The gap none of these fills is: on-premises deployment that makes CUI handling tractable, automated evidence collection that reduces engineering hours, continuous validation that keeps the SSP and the system in sync, and pricing that fits a 45-person contractor's budget. That's the gap Intranest is built for.

## The thesis: the connector layer is the product

Most compliance platforms sell themselves on the things compliance officers want to talk about — the SSP generation engine, the POA&M auto-builder, the assessment-readiness dashboard, the evidence repository. Intranest does all of this, and the architecture is sound, but none of it is the differentiator.

The differentiator is the connector layer. Software that sits inside the customer's network, holds credentials to their existing security tooling, pulls evidence from those tools on a schedule, and produces continuously-current compliance state. Everything else in the platform — SSP generation, POA&M, scoring, the assessment-readiness dashboard — is downstream of the evidence the connector layer collects.

This framing matters because it determines what the platform is competing on. If Intranest is a CMMC compliance tool with some integrations, it's competing with Totem at $5,000 per year and losing on feature breadth. If Intranest is a sovereign continuous compliance platform whose connectors run inside the customer's network and produce live evidence against the customer's actual systems, it's competing with Drata in a market segment Drata can't legally serve, at a price point Drata can't reach.

The connector layer is the wedge that converts CMMC compliance from a documentation exercise into an evidence-collection exercise. That's the product. The rest of the platform is what makes the evidence usable.

## How the platform is structured

The connector layer is built as a small set of orthogonal abstractions, each of which earns its place by being load-bearing for a specific concern.

`BaseConnector` is the abstract base class every connector inherits from. It defines four contract methods — `credentials_schema`, `setup_component`, `pull`, `test_connection` — and a fifth that aggregates errors across pulls (`get_pull_errors`). The `credentials_schema` returns a list of typed field definitions (text, password, select, textarea) that the frontend renders into a setup wizard automatically. New connectors don't need bespoke frontend code unless they have configuration that doesn't fit the four-field-type schema; that escape hatch exists but hasn't been needed yet.

`PulledEvidence` is the dataclass returned by `pull`. It carries the evidence content, the control IDs the evidence supports, metadata about how the evidence was collected, and five optional fields that describe the evidence's epistemological posture: `coverage_scope` (full or partial), `missing_sources` (free-form list of what's not covered), `evidence_directness` (raw configuration vs Microsoft-derived aggregate), `degraded` (boolean for "we got something but it wasn't complete"), and `degradation_reason` (free-form text). These fields exist because real-world evidence collection is rarely all-or-nothing. A SharePoint license might be missing on a tenant; a Microsoft Secure Score is an aggregate scoring derivative rather than raw configuration; an audit log query might fail terminally because the tenant has audit logging administratively disabled. The platform can't lie about these conditions, and the SSP narrative pipeline downstream needs to know about them so it can render them as honest narrative rather than fabricated coverage claims.

The `_msgraph` helper layer at `src/connectors/_msgraph/` is the reusable foundation underneath every Microsoft Graph connector. It centralizes cloud routing through a `CloudEnvironment` enum (commercial, GCC High, DOD), token management via MSAL, sync HTTP client with token cache and pagination, beta-endpoint routing, and — the load-bearing piece — capability-gap detection. The same code paths serve `EntraIdConnector` and `M365GccHighConnector` and will serve future Microsoft connectors without re-discovery. The cloud-routing layer means the same connector code runs against `graph.microsoft.com`, `graph.microsoft.us`, and `dod-graph.microsoft.us` with one credential field flipped — the customer in a GCC High tenant doesn't get a different code path, just a different routing decision made at the URL-construction layer.

The capability-gap detection framework deserves its own treatment because it's the architectural primitive that distinguishes platforms that have been run against real tenants from platforms that have only been run against documentation.

## Empirical discipline

The four-detector capability-gap framework is the most concrete example of the platform's empirical posture, and it's also the strongest evidence the architecture has been tested against real-world Microsoft.

Microsoft Graph signals tenant-level service unavailability through at least four different shapes, depending on which underlying service is involved. The first signal — 403 with `error.code = "Forbidden_LicensingError"` — is what the Microsoft documentation suggests happens when a tenant lacks a license for a service. This is what the framework was originally built around, hypothesized from documentation. It has not yet been observed in production.

The second signal — 400 with `error.code = "BadRequest"` and a descriptive message containing fragments like "does not have a SPO license" or "Request not applicable to target tenant" — is what actually happens when a tenant lacks SharePoint Online or Intune provisioning. This was discovered live during F.3a's pull of MP.L2-3.8.1 against a trial tenant with no SharePoint license. The detection helper was added as a narrow-signature amendment to the retry layer, complementary to the licensing detector rather than replacing it.

The third signal — 500 with `error.code = "generalException"` and an `innerError.message` containing "didn't accept the auth token" — is what happens when the Purview / InformationProtection backend (Microsoft's internal "PolicyProfile" service) is unprovisioned. This was discovered live during F.3b's pull of sensitivity-label data. Different shape, same underlying cause, different detection logic, third detector added.

The fourth signal — 400 with `error.code = "UnknownError"` and an embedded JSON-as-string in `error.message` containing "AuditingDisabledTenant" — is what happens when a tenant has unified audit logging administratively disabled. This was discovered live during F.3c's first POST through the async query helper to `/security/auditLog/queries`. It's categorically different from the previous three: it's a tenant configuration choice rather than a license or provisioning gap, and it can be remediated by the customer toggling a setting.

All four signals raise a single exception class to connector code (`MsGraphCapabilityError`), so connectors handle one error path regardless of which underlying detector fired. The detectors live in one module, get added incrementally as new shapes are discovered, and are never silently absorbed into existing detectors when a new shape appears. That last discipline matters: when F.3c hit the audit-disabled signal, the empirically-correct response was to add a fourth narrow detector, not to widen one of the existing three to also match. The detectors are narrow on purpose so they don't false-positive on real errors.

This level of detail belongs in this document not because the four detectors are uniquely interesting, but because they're concrete. A platform claiming to handle "real-world Microsoft tenant variability" should be able to enumerate the actual variability it has handled, with the error response shapes that drove each design decision. Intranest can. That's evidence the architecture has been tested where it matters, against tenants with mixed service provisioning, with the discipline to add detection rather than swallow exceptions when reality didn't match the documentation.

## Continuous validation

Everything the platform does today is point-in-time. A connector runs, pulls evidence, emits artifacts. An assessor or compliance officer reviews the artifacts. An SSP is generated from the latest evidence. This works, but it's not continuous compliance — it's scheduled re-collection.

Continuous compliance means the platform notices when something changes between runs and surfaces that change as a state transition the customer can act on. If the customer's Entra tenant has three users in a privileged group on Monday and four users on Tuesday, the platform should know that on Tuesday, classify the change as a posture-affecting event, transition the relevant control's state from compliant to drifting, and notify the customer's compliance officer before they discover it during the next assessment cycle.

The architectural pieces required for this are tractable. A `connector_run_diffs` table stores per-control diffs between sequential runs, with diff strategies that vary by data shape — set comparison for user lists, value comparison for configuration fields, event-stream comparison for time-windowed audit data. A `control_states` table tracks per-control state with transitions driven by diff events: compliant, drifting, degraded, and the inverse path remediating. State transitions trigger notification delivery and audit-log entries. The customer-visible dashboard shows live posture rather than a snapshot.

This work hasn't shipped yet. It's the layer above the current evidence-collection foundation, and it's what turns the platform from a compliance document generator into a compliance operating system. The CrowdStrike connector planned for the next major implementation pass is the first connector designed to consume these primitives — its data is inherently temporal (detection events, prevention policy changes, device compliance state) and the controls it supports are continuous-state controls where the question isn't "is this configured?" but "is this currently working?" Building delta detection alongside the CrowdStrike connector means the primitives are tested against the right data shape from the start, rather than retrofitted onto controls whose evidence was modeled as point-in-time snapshots.

When the continuous-validation layer ships, the platform's pitch changes. Today's demo is "look at what we pull from real Microsoft tenants without exfiltrating CUI." The post-CrowdStrike demo is "look at the platform notice your tenant configuration drift in near-real-time and surface it to your compliance officer before your next assessment." That's a categorical shift in what the product is.

## What this isn't, against the alternatives

It's worth being specific about what each existing category does well and where it fails, because the positioning argument depends on the failures being real rather than rhetorical.

Drata, Vanta, Sprinto, and Secureframe are operationally excellent for organizations whose data can live in commercial multi-tenant SaaS. Their integration breadth, continuous monitoring, real-time dashboards, and developer-friendly APIs are best-in-class. They are also disqualified from serving CUI handlers by their architecture, not by a feature gap. No amount of feature parity changes the regulatory posture. Intranest is not trying to compete with them on commercial SOC 2 — it's trying to be what they architecturally cannot be, for customers they architecturally cannot serve.

Totem, PreVeil GRC, FutureFeed, and the CMMC-purpose-built tools have the regulatory positioning right and serve a real market segment. They don't automate evidence collection, don't validate evidence integrity, and don't produce continuously-current compliance state. The customer's compliance posture is whatever they last manually documented, which means it drifts from reality between manual updates. Adequate for low-rigor self-assessment; insufficient for high-rigor C3PAO assessment, which is where the market is heading. PreVeil specifically is a meaningful adjacent tool — many small DIB contractors use it as their primary email/file environment instead of Microsoft GCC High, and a future PreVeil connector is high on the post-Microsoft roadmap.

Archer, ServiceNow GRC, and the enterprise on-prem GRC suites have the deployment posture right and the operational maturity to support continuous compliance, but their pricing and implementation overhead exclude the small DIB segment by design. Their target customer is the Fortune 500 enterprise; the 45-person subcontractor is not in their funnel.

The consultant model produces documents, not systems. A $30,000 SSP engagement produces an artifact that's accurate on the day of signing and increasingly inaccurate thereafter. This is the model most small DIB contractors actually use today, and it's the model most directly displaced by what Intranest is building. The consultant's value isn't the SSP itself — it's the assessment expertise embedded in the SSP. Intranest doesn't replace that expertise; it makes the resulting documents continuously current and the underlying evidence assessor-ready.

## Sovereign deployment

The deployment posture is a first-class concern, not an afterthought. The connector layer running inside the customer's network is the architectural commitment that makes the regulatory positioning work, and it has implications throughout the stack.

Today, the platform runs as two cloud-hosted services — frontend on Vercel, backend on Render — with a sovereign inference path planned for production where vLLM and Llama 3.3 70B run on customer-controlled GPU. The intermediate state that ships first is hybrid: the control plane runs in a Render-equivalent environment that the customer trusts, but the connector layer and the LLM inference both run inside the customer's network. CUI-adjacent metadata never crosses the customer's perimeter.

The end-state deployment is a Helm-installable platform that runs entirely on customer-controlled infrastructure. This includes the FastAPI control plane, the Postgres system of record, the Qdrant vector store, the connector runtime, the LLM inference layer, and the customer-side observability stack. The customer's procurement officer evaluating the platform should see an architecture document that says, accurately: nothing leaves your network except aggregated compliance state to your own monitoring infrastructure. That's the procurement story that competitors with multi-tenant SaaS architectures cannot match.

The credentials story sits inside this. Today's platform uses Fernet encryption with an environment-variable-backed key. The end-state credential storage uses customer-controlled key management — HashiCorp Vault, AWS KMS in the customer's account, Azure Key Vault in the customer's tenant — with the platform never holding plaintext keys and credential access logged in the customer's audit trail. The path between today and that end-state is a `CredentialProvider` abstraction that connectors call, with the current direct-Fernet path becoming the development-mode fallback once the abstraction lands.

## Future state

The platform's first vertical is CMMC. The architectural decisions — sovereign deployment, capability-gap detection, framework-agnostic evidence model, continuous validation primitives — are not CMMC-specific. They are what makes compliance software work for organizations that can't put their data in multi-tenant SaaS GRC.

The natural vertical expansions are NIST 800-53 (federal civilian agency contracts, FedRAMP suppliers — same buyer profile as DIB, more contracts) and ISO 27001 (commercial markets where regulated data still can't go to cloud GRC — healthcare, financial services, critical infrastructure). The technical work for both is the OLIR crosswalk pattern: an internal control taxonomy with framework mappings, framework-agnostic evidence collection, framework-aware document generation. The evidence model needs to be designed for this from the start, even though only 800-171 mappings exist today; retrofitting it later means refactoring every connector's evidence-emit logic.

The strategic decision for vertical expansion is downstream of CMMC traction. Build the CMMC vertical excellently, get paying customers, learn what they actually need, then expand. The architectural foundation needs to be there now so the expansion is feature work rather than refactor work, but the actual expansion is post-customer-fit work, not pre-launch work.

## What this is for

Intranest exists because there's a category of compliance work — sovereign continuous compliance for regulated industries — that no existing platform serves well. The CMMC vertical is the wedge because the regulatory pressure is real and immediate and the existing options are obviously inadequate. The connector layer is the product because evidence collection is what the existing options don't do, and automating it is what makes the platform pay for itself.

The goal is not to be a smaller, cheaper Drata. The goal is to be the platform that Drata can't be, for the customers Drata can't serve, in a market segment Drata doesn't enter. The architectural commitments — sovereign deployment, capability-gap detection, continuous validation, framework-agnostic evidence — are the operationalization of that goal.

What's been built so far is the foundation: the connector framework, the Microsoft Graph helper layer empirically validated against real tenants, the evidence model that captures the messiness of real-world data collection, and the discipline (sub-pass pre-split, default-respect contract, inline live smoke per sub-pass, carryover-as-commit-message) that has produced five working controls on each of two connectors with zero hallucinated data and a verifiable audit chain. What's next is the layer that turns evidence collection into continuous validation: delta detection, state machines, drift alerts, and the dashboard that makes the platform operationally visible to a customer's compliance officer.

When that layer ships, the platform becomes demonstrable as continuous compliance rather than scheduled re-collection. That's the platform Intranest is for.
