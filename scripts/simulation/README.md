# Simulation Fixtures

This directory contains simulation fixtures for verifying the Intranest CMMC
platform against known-good customer scenarios.

## Structure

```
scripts/simulation/
├── README.md                         # this file
├── schema/                           # code-extracted ground truth
│   ├── intake_schema.yaml            # 135 questions across 9 modules (110 controls)
│   ├── evidence_types.yaml           # evidence type taxonomy + freshness thresholds
│   ├── scan_formats.yaml             # Nessus XML + CIS-CAT JSON expected shapes
│   ├── contradiction_rules.yaml      # 14 family-level contradiction rules
│   └── baseline_catalog.yaml         # 45 CIS items (25 Win11 + 20 M365)
├── fixtures/
│   └── meridian_aerospace/           # Phase 2: hand-authored customer scenario
├── loader/                           # Phase 3: fixture validator + loader
└── report/                           # Phase 3: pass/fail verification output
```

## Phases

- **Phase 1** (current): Extract schema from source code, scaffold directories.
  Regenerate schema files when intake modules change.
- **Phase 2**: Author the Meridian Aerospace fixture — 135 intake answers,
  evidence artifacts, Nessus + CIS-CAT scan specs, contradictions, and
  expected-platform-outputs assertion block.
- **Phase 3**: Build the fixture loader and verification harness that validates
  platform outputs against fixture expectations.

## Schema Regeneration

If intake modules change, regenerate `intake_schema.yaml`:

```bash
cd d:/cmmc-platform
python -c "
import yaml, sys; sys.path.insert(0, '.')
from src.api.intake_modules import get_all_modules
# ... (see extraction script in Phase 1 commit)
"
```

Other schema files are hand-maintained but derived from source.
