CMMC Platform — Figma Design Reference
Version: March 25, 2026

Product identity
Name: Sovereign CMMC Compliance Platform Tagline: Evidence-first compliance operating system Target user: IT director or security lead at a 20-80 person defense contractor Primary action: Upload docs → answer questions → get assessment-ready package

Tech stack (affects design constraints)
Frontend: React 19 + Vite (localhost:5173)
Backend: FastAPI (localhost:8001)
UI library: No component library — custom components
Icons: Lucide React
Charts: Recharts (or similar)
No Tailwind CSS compiler — using utility classes from CDN
Navigation structure
AppShell.jsx — persistent left sidebar, 220px wide

Sidebar nav items (top to bottom):

Onboarding (NEW) — /onboarding — blue accent, appears for new orgs
Overview — / — main dashboard
SSP — /ssp — SSP viewer
Evidence — /evidence — artifact manager
POA&M — /poam — remediation tracking
Setup wizard — /intake — module questionnaires
Settings — /settings — health + audit chain
Sidebar footer: org name, org ID, version number

Page inventory (7 pages)
Page 1: Overview.jsx (859 lines) — route: /
Compliance dashboard. First thing users see after onboarding.

Components:

SPRS gauge — radial/circular, score 0-110, color-coded (red < 50, amber 50-80, green 80+)
4 metric cards (controls met, evidence published, POA&M open, audit entries)
Family coverage bar chart — 14 horizontal bars, each split into met/partial/gap segments
Critical gaps table — control ID, gap type, severity badge, points at risk
POA&M summary widget — open/in-progress/overdue counts with colored dots
Page 2: SSP.jsx (819 lines) — route: /ssp
All 110 SSP sections grouped by 14 families. Expandable cards.

Components:

Family dropdown filter (14 families)
Status filter pills (met / partial / not met)
Search bar
Expandable control cards: control ID, title, status badge, point value, evidence ref count. Expands to: full implementation narrative, evidence citations (linked), identified gaps
Page 3: Evidence.jsx (651 lines) — route: /evidence
Evidence artifact lifecycle manager.

Components:

Upload button
State filter pills: DRAFT (gray) / REVIEWED (blue) / APPROVED (amber) / PUBLISHED (green)
Evidence type filter dropdown
Artifact table rows: filename, type badge, state badge, linked control count, SHA-256 hash (published only), file size
Row actions: transition state, verify hash, view details, download
Page 4: Intake.jsx (784 lines) — route: /intake
Guided TurboTax-style questionnaire. One question per screen.

Layout: 2-column — sidebar (220px) + main question area Sidebar: module selector (M0/M1/M10), section progress list, completion badges Main area: progress bar, question text, answer options, help text, control ID tags, back/next buttons

Answer types:

single_choice: radio button cards, one selectable
multi_choice: checkbox cards, multiple selectable
text_input: textarea for free-text (names, descriptions)
number_input: number field with optional min/max
Visual indicators:

Gap severity badges on options (CRITICAL=red, HIGH=amber, MEDIUM=yellow)
Alert banner when gap-triggering option selected
Control ID pills (monospace, small, gray background)
Strikethrough on skipped sections (adaptive mode)
Page 5: POAMPage.jsx (396 lines) — route: /poam
Plan of Action & Milestones tracking.

Components:

Status filter: OPEN / IN_PROGRESS / CLOSED / OVERDUE
Generate POA&M button
Item rows: ID, control ID, weakness description, risk level badge, status badge, due date, days remaining
Overdue highlight (red border or background tint)
Page 6: Settings.jsx (380 lines) — route: /settings
System health and integrity verification.

Components:

4 service health cards: Postgres, Qdrant, Temporal, LLM — status dot + label
Audit chain section: entry count, "Chain intact" badge, verify button
Hash manifest section: published count, "All verified" badge, export button
Page 7 (NEW): Onboarding.jsx — route: /onboarding
5-step customer onboarding wizard. The primary product entry point.

Layout: horizontal step indicator (pills) at top, main content below. Steps are clickable for completed steps. No sidebar.

Step 1 — Upload:

Large drag-and-drop zone (dashed 2px border, centered icon + text)
Uploaded file list: filename, size, status pill (Pending → Analyzing → Analyzed → Failed)
"Skip — I don't have any documents" link
"Analyze documents" primary button
Step 2 — Analysis results:

3 metric cards: controls covered (green), gaps remaining (amber), claims extracted (blue)
Coverage progress bar: green (covered) + amber (partial) + gray (gap) segments
Legend below bar
Per-document cards: filename, category badge (ir_plan, policy, scan_report, etc.), claim count, 2-line AI summary, control IDs covered
Step 3 — Targeted questions:

Info banner: "Based on your documents, we need X questions (skipped Y)"
Same wizard layout as Intake.jsx
Skipped sections shown with strikethrough + "covered by uploads" note
Active questions identical to Intake question cards
Step 4 — Generation plan:

7 template rows, each with: document name + action badge
Action badges:
SKIP (green): "Your upload covers this"
SUPPLEMENT (amber): "Will generate for N gap controls"
GENERATE (blue): "Will generate from your answers"
Summary line: "Skip 1, supplement 1, generate 5. ~15 minutes."
"Generate documents" primary button
Generation progress: per-template progress with status
Step 5 — Review:

3 metric cards: controls covered, documents total, estimated SPRS
Document list: each row has document name, source tag (uploaded/generated/supplemented), control count, word count, "Start review" button
"Go to compliance dashboard" primary button at bottom
Design tokens
Colors
Purpose	Color	Usage
Success / covered / MET	Green	Badges, bar segments, published state
Warning / partial	Amber	Badges, bar segments, approved state
Danger / gap / CRITICAL	Red	Badges, alerts, overdue
Info / active / in progress	Blue	Buttons, links, reviewed state
Neutral / draft	Gray	Badges, empty states
Evidence state machine
State	Color	Icon
DRAFT	Gray	Pencil
REVIEWED	Blue	Eye
APPROVED	Amber	Check
PUBLISHED	Green	Lock
Gap severity
Level	Color	Points
CRITICAL	Red	5-point controls
HIGH	Amber/orange	3-point controls
MEDIUM	Yellow/muted	1-point controls
Typography
Element	Size	Weight
Page title	20px	500
Section header	16px	500
Body text	14px	400
Small label	12px	400, muted
Monospace (IDs, hashes)	11px	mono
Metric card number	24-28px	500
Spacing
Element	Value
Page padding	24px
Card padding	16px
Card gap	12px
Section gap	24px
Sidebar width	220px
Border radius (cards)	12px
Border radius (badges)	16px (pill)
Border width	0.5px
User flows
New customer (primary)
/onboarding → upload docs → see analysis → answer ~18 questions → review generation plan → generate → review docs → /evidence (publish) → / (dashboard)

Returning customer
/ (dashboard) → /ssp (view SSP) → /evidence (manage) → /intake (more questions) → /poam (track remediation)

Assessment prep
/ (check SPRS) → /evidence (verify all published) → /ssp (download) → /settings (verify audit chain) → export binder ZIP

Screen specs
Design width: 1440px
Sidebar: 220px fixed left
Content area: 1220px max
Mobile: not supported (enterprise desktop product)
Min width: 1024px
Data reference
Metric	Value
Total controls	110
Control families	14
Assessment objectives	246
Document templates	7
SPRS score range	-203 to 110
Evidence states	4
Intake modules	3 (M0: 16q, M1: 28q, M10: 29q)
Total questions	73
Database tables	17 (14 existing + 3 new)
API routes	50+
Demo org (Apex Defense Solutions)
45 employees, Columbia MD
Entra ID + MFA, M365 GCC High, CrowdStrike Falcon, Palo Alto PA-450
Sentinel SIEM, VLAN segmentation, BitLocker, KnowBe4, Jira
CUI: Technical data (ITAR), specifications, test results
SPRS: 63-68 raw / 110 conditional
26 published artifacts, 35-37 open POA&Ms, 145+ audit entries