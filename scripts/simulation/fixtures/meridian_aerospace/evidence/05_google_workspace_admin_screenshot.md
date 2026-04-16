---
artifact_id: meridian_ev_05
title: Google Workspace Admin Console — 2-Step Verification Screenshot
evidence_type: SCREENSHOT
file_format: png
page_count: 1
last_updated: "2026-01-15"
owner: jbell@meridian-aero.com
maps_to_controls: [IA.L2-3.5.3]
content_summary: |
  This artifact is a single PNG screenshot of the Google Workspace Admin
  Console captured on January 15, 2026. The screenshot shows the
  Security > Authentication > 2-Step Verification settings page for the
  meridian-aero.com organizational unit.

  The visible settings confirm that 2-Step Verification is set to
  "Enforced" at the organization level, meaning all 14 user accounts under
  the meridian-aero.com domain are required to enroll in 2-Step
  Verification to access their Google Workspace accounts. The enforcement
  date shown is September 2025.

  The screenshot shows the enrollment status summary: 14 of 14 users
  enrolled. The allowed second-factor methods visible in the screenshot
  include "Any" (security keys, Google prompts, text message codes, and
  authenticator app codes). There is no restriction to phishing-resistant
  methods only — SMS-based codes are permitted as a second factor.

  The browser tab and URL bar are partially visible, confirming the page
  is admin.google.com. The logged-in admin account shown is
  jbell@meridian-aero.com.

  DELIBERATELY ABSENT: The screenshot does NOT show the status of legacy
  protocols such as IMAP, SMTP, and POP access. These "less secure app"
  settings are on a different admin console page and are not captured in
  this artifact. This gap is significant because if legacy IMAP/SMTP
  authentication is still enabled, it bypasses 2-Step Verification
  entirely, which is the specific misconfiguration that the Nessus scan
  finding IA_01 identifies. The screenshot also does not show session
  duration or timeout settings, password complexity requirements, or any
  conditional access policies. There is no evidence of whether Google
  Advanced Protection Program is enabled for any accounts.
---
