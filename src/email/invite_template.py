"""Invite email body + subject builders.

Brand:
  bg          #0a0f1a
  panel       rgba(24,24,27,1)
  border      rgba(255,255,255,0.08)
  text        rgba(255,255,255,0.9)
  text-muted  rgba(255,255,255,0.6)
  text-faint  rgba(255,255,255,0.4)
  teal        #27DCDD
  teal deep   #1C7C97

Email clients butcher modern CSS, so the template uses inline styles + a
single linear-gradient on the CTA. Plain-text fallback at the bottom for
clients that strip HTML.
"""
from __future__ import annotations

from typing import Optional


def build_invite_email_subject(org_name: Optional[str]) -> str:
    if org_name and org_name.strip():
        return f"You've been invited to Intranest by {org_name.strip()}"
    return "You've been invited to Intranest"


def build_invite_email_html(
    invitee_name: Optional[str],
    invite_link: str,
    org_name: Optional[str] = None,
) -> str:
    """Render the invite email body. Returns a complete HTML document."""
    greeting_name = (invitee_name or "").strip() or "there"
    org_clause = (
        f"<strong style=\"color:#fff;\">{_escape(org_name.strip())}</strong> "
        f"has invited you to join their CMMC compliance workspace on Intranest."
        if org_name and org_name.strip()
        else "You've been invited to join Intranest, the sovereign CMMC compliance platform for defense contractors."
    )
    safe_link = _escape(invite_link)

    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>You've been invited to Intranest</title>
  </head>
  <body style="margin:0; padding:0; background:#0a0f1a; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif; color:rgba(255,255,255,0.9);">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#0a0f1a;">
      <tr>
        <td align="center" style="padding:40px 16px;">
          <table role="presentation" width="560" cellpadding="0" cellspacing="0" style="max-width:560px; width:100%; background:rgba(24,24,27,1); border:1px solid rgba(255,255,255,0.08); border-radius:12px;">
            <tr>
              <td style="padding:32px 32px 8px 32px;">
                <div style="font-size:13px; letter-spacing:0.08em; text-transform:uppercase; color:#27DCDD; font-weight:600;">
                  Intranest
                </div>
              </td>
            </tr>
            <tr>
              <td style="padding:8px 32px 24px 32px;">
                <h1 style="margin:0 0 16px 0; font-size:22px; font-weight:600; color:rgba(255,255,255,0.95); line-height:1.3;">
                  Hi {_escape(greeting_name)},
                </h1>
                <p style="margin:0 0 16px 0; font-size:15px; line-height:1.55; color:rgba(255,255,255,0.85);">
                  {org_clause}
                </p>
                <p style="margin:0 0 28px 0; font-size:15px; line-height:1.55; color:rgba(255,255,255,0.6);">
                  Click the button below to accept the invitation and finish setting up your account. The link expires in 7 days.
                </p>
                <table role="presentation" cellpadding="0" cellspacing="0" style="margin:0 0 24px 0;">
                  <tr>
                    <td style="background:linear-gradient(135deg,#1C7C97 0%,#27DCDD 100%); border-radius:8px;">
                      <a href="{safe_link}" target="_blank" style="display:inline-block; padding:13px 28px; font-size:15px; font-weight:600; color:#0a0f1a; text-decoration:none; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;">
                        Accept invitation
                      </a>
                    </td>
                  </tr>
                </table>
                <p style="margin:0 0 8px 0; font-size:12px; color:rgba(255,255,255,0.4);">
                  If the button doesn't work, copy and paste this link into your browser:
                </p>
                <p style="margin:0; font-size:13px; word-break:break-all;">
                  <a href="{safe_link}" target="_blank" style="color:#27DCDD; text-decoration:underline;">{safe_link}</a>
                </p>
              </td>
            </tr>
            <tr>
              <td style="padding:24px 32px 32px 32px; border-top:1px solid rgba(255,255,255,0.06);">
                <p style="margin:0; font-size:11px; color:rgba(255,255,255,0.4); line-height:1.5;">
                  Intranest — sovereign CMMC compliance for defense contractors. CUI never leaves your network. SHA-256 evidence integrity, AI-generated SSP narratives, continuous compliance monitoring.
                </p>
                <p style="margin:12px 0 0 0; font-size:11px; color:rgba(255,255,255,0.3);">
                  Didn't expect this invitation? You can ignore this email — the link is single-use and expires automatically.
                </p>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>"""


def _escape(value: str) -> str:
    """Minimal HTML escape — names/orgs are user-supplied, the link is too."""
    return (
        value.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;")
             .replace('"', "&quot;")
             .replace("'", "&#39;")
    )
