"""Email alert delivery module.

Uses a file-based outbox for testing (no real SMTP server required).
Each "sent" email is written as a JSON file to the email_outbox/ directory.
"""

import os
import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

EMAIL_OUTBOX_DIR = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'email_outbox')


def send_alert_email(user_email, user_name, signal_title, signal_summary,
                     severity, anomaly_score, category, signal_url=None):
    """Send an alert email. Uses file-based outbox for testing.

    Parameters
    ----------
    user_email : str
        Recipient email address.
    user_name : str
        Recipient display name.
    signal_title : str
        Title of the signal that triggered the alert.
    signal_summary : str | None
        Short summary of the signal.
    severity : str
        One of: critical, high, medium, low.
    anomaly_score : float
        Anomaly score in [0, 1].
    category : str
        Signal category (e.g. "finance", "cyber").
    signal_url : str | None
        Deep-link into the OracleFlow platform.

    Returns
    -------
    str
        Path to the outbox JSON file that was written.
    """
    os.makedirs(EMAIL_OUTBOX_DIR, exist_ok=True)

    timestamp = datetime.now(timezone.utc).isoformat()
    filename = f"{timestamp.replace(':', '-')}_{user_email}.json"

    email_data = {
        "to": user_email,
        "to_name": user_name,
        "subject": f"[OracleFlow {severity.upper()}] {signal_title}",
        "timestamp": timestamp,
        "body_text": (
            f"ALERT: {signal_title}\n\n"
            f"Severity: {severity}\n"
            f"Category: {category}\n"
            f"Anomaly Score: {anomaly_score}\n\n"
            f"{signal_summary or 'No summary available.'}\n\n"
            f"View in OracleFlow: {signal_url or 'https://app.oracleflow.io/signals'}"
        ),
        "body_html": _build_html_email(
            user_name, signal_title, signal_summary,
            severity, anomaly_score, category, signal_url,
        ),
    }

    filepath = os.path.join(EMAIL_OUTBOX_DIR, filename)
    with open(filepath, 'w') as f:
        json.dump(email_data, f, indent=2)

    logger.info(f"Email alert queued: {filepath}")
    return filepath


def _build_html_email(name, title, summary, severity, score, category, url):
    """Build a styled HTML email body for the alert."""
    sev_color = {
        'critical': '#ef4444',
        'high': '#f97316',
        'medium': '#eab308',
        'low': '#22c55e',
    }.get(severity, '#888')

    score_pct = int(score * 100) if score is not None else 0

    return f"""
    <div style="font-family: 'Helvetica Neue', sans-serif; max-width: 600px; margin: 0 auto; background: #0a0a0a; color: #e8e8e8; padding: 32px;">
        <div style="border-bottom: 1px solid #333; padding-bottom: 16px; margin-bottom: 24px;">
            <span style="font-family: monospace; font-weight: 800; letter-spacing: 2px; font-size: 14px;">ORACLEFLOW</span>
        </div>
        <div style="display: inline-block; background: {sev_color}; color: white; padding: 4px 12px; font-size: 12px; font-weight: 700; letter-spacing: 1px; margin-bottom: 16px; font-family: monospace;">{severity.upper()}</div>
        <div style="display: inline-block; background: transparent; border: 1px solid #FF4500; color: #FF4500; padding: 4px 12px; font-size: 12px; font-family: monospace; margin-left: 8px;">{category.upper()}</div>
        <h2 style="font-size: 20px; margin: 16px 0 8px; color: #e8e8e8;">{title}</h2>
        <p style="color: #999; font-size: 14px; line-height: 1.6;">{summary or 'A significant change has been detected.'}</p>
        <div style="margin: 24px 0; background: #1a1a1a; padding: 16px; border: 1px solid #333;">
            <span style="font-family: monospace; font-size: 12px; color: #888;">ANOMALY SCORE</span>
            <div style="background: #333; height: 8px; margin-top: 8px; border-radius: 4px; overflow: hidden;">
                <div style="background: {sev_color}; height: 100%; width: {score_pct}%;"></div>
            </div>
            <span style="font-family: monospace; font-size: 18px; font-weight: 700; color: {sev_color};">{score_pct}%</span>
        </div>
        <a href="{url or 'https://app.oracleflow.io/signals'}" style="display: inline-block; background: #FF4500; color: white; padding: 12px 24px; font-family: monospace; font-weight: 700; font-size: 14px; text-decoration: none; letter-spacing: 0.5px;">View in OracleFlow &rarr;</a>
        <div style="margin-top: 32px; padding-top: 16px; border-top: 1px solid #333; font-size: 12px; color: #666;">
            You received this because your alert rules matched this signal. Manage alerts in Settings.
        </div>
    </div>"""


def list_outbox_emails(limit=50):
    """List emails in the outbox directory, newest first.

    Returns a list of dicts with email metadata (without full HTML body).
    """
    if not os.path.isdir(EMAIL_OUTBOX_DIR):
        return []

    files = sorted(os.listdir(EMAIL_OUTBOX_DIR), reverse=True)
    emails = []
    for fname in files[:limit]:
        if not fname.endswith('.json'):
            continue
        fpath = os.path.join(EMAIL_OUTBOX_DIR, fname)
        try:
            with open(fpath, 'r') as f:
                data = json.load(f)
            emails.append({
                "filename": fname,
                "to": data.get("to"),
                "to_name": data.get("to_name"),
                "subject": data.get("subject"),
                "timestamp": data.get("timestamp"),
                "body_text": data.get("body_text"),
            })
        except Exception:
            continue

    return emails
