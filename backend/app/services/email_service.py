import httpx
import logging
import smtplib
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from app.config import get_settings

logger = logging.getLogger("email_service")
settings = get_settings()


async def send_email_via_smtp(to_email: str, subject: str, html_body: str) -> tuple:
    if not all([settings.SMTP_HOST, settings.SMTP_USERNAME, settings.SMTP_PASSWORD]):
        return False, "SMTP not fully configured (host, username, password required)"

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_FROM_EMAIL or settings.SMTP_USERNAME
        msg["To"] = to_email
        msg.attach(MIMEText(html_body, "html"))

        def _send():
            if settings.SMTP_USE_TLS:
                server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15)
                server.ehlo()
                server.starttls()
                server.ehlo()
            else:
                server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15)
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.sendmail(msg["From"], [to_email], msg.as_string())
            server.quit()

        await asyncio.to_thread(_send)
        logger.info(f"Email sent to {to_email} via SMTP ({settings.SMTP_HOST})")
        return True, ""
    except Exception as e:
        error_msg = f"SMTP send failed: {type(e).__name__}: {e}"
        logger.error(error_msg)
        return False, error_msg


async def send_email_via_sendgrid(to_email: str, subject: str, html_body: str) -> tuple:
    if not settings.SENDGRID_API_KEY:
        return False, "SENDGRID_API_KEY not configured"

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                "https://api.sendgrid.com/v3/mail/send",
                json={
                    "personalizations": [{"to": [{"email": to_email}]}],
                    "from": _parse_email(settings.SENDGRID_FROM_EMAIL),
                    "subject": subject,
                    "content": [{"type": "text/html", "value": html_body}],
                },
                headers={
                    "Authorization": f"Bearer {settings.SENDGRID_API_KEY}",
                    "Content-Type": "application/json",
                },
            )
            if resp.status_code in (200, 202):
                logger.info(f"Email sent to {to_email} via SendGrid")
                return True, ""
            error_msg = f"SendGrid API error {resp.status_code}: {resp.text[:300]}"
            logger.error(error_msg)
            return False, error_msg
    except Exception as e:
        error_msg = f"SendGrid send failed: {type(e).__name__}: {e}"
        logger.error(error_msg)
        return False, error_msg


async def send_email_via_resend(to_email: str, subject: str, html_body: str) -> tuple:
    if not settings.RESEND_API_KEY:
        return False, "RESEND_API_KEY not configured"

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                "https://api.resend.com/emails",
                json={
                    "from": settings.RESEND_FROM_EMAIL,
                    "to": [to_email],
                    "subject": subject,
                    "html": html_body,
                },
                headers={
                    "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                    "Content-Type": "application/json",
                },
            )
            if resp.status_code == 200:
                body = resp.json()
                email_id = body.get('id', 'N/A')
                logger.info(f"Email sent to {to_email} via Resend: id={email_id}")

                if "onboarding@resend.dev" in settings.RESEND_FROM_EMAIL:
                    logger.warning(
                        "Resend is in TEST MODE (onboarding@resend.dev). "
                        "Emails are only delivered to your Resend account's verified email address. "
                        "External recipients like Gmail will NOT receive emails. "
                        "Add a verified domain at https://resend.com/domains to send to real users."
                    )
                return True, ""
            error_msg = f"Resend API error {resp.status_code}: {resp.text[:300]}"
            logger.error(error_msg)
            return False, error_msg
    except Exception as e:
        error_msg = f"Resend send failed: {type(e).__name__}: {e}"
        logger.error(error_msg)
        return False, error_msg


def _parse_email(from_str: str) -> dict:
    import re
    match = re.match(r'^(.+?)\s*<(.+?)>$', from_str.strip())
    if match:
        return {"name": match.group(1).strip(), "email": match.group(2).strip()}
    return {"email": from_str.strip()}


async def send_email(to_email: str, subject: str, html_body: str, *, test_each: bool = False) -> tuple:
    providers = []
    if settings.SMTP_HOST and settings.SMTP_USERNAME:
        providers.append(("SMTP", send_email_via_smtp))
    if settings.SENDGRID_API_KEY:
        providers.append(("SendGrid", send_email_via_sendgrid))
    if settings.RESEND_API_KEY:
        providers.append(("Resend", send_email_via_resend))

    if not providers:
        msg = "No email provider configured — set SMTP_HOST+SMTP_USERNAME, SENDGRID_API_KEY, or RESEND_API_KEY"
        logger.warning(msg)
        return False, msg

    if test_each:
        provider_results = {}
        for name, func in providers:
            sent, err = await func(to_email, subject, html_body)
            provider_results[name] = {"success": sent, "error": err}
        return not all(not r["success"] for r in provider_results.values()), str(provider_results)

    for name, func in providers:
        sent, err = await func(to_email, subject, html_body)
        if sent:
            return True, ""
        logger.warning(f"{name} failed: {err}")

    return False, f"All email providers failed"


async def send_password_reset_email(to_email: str, reset_token: str, frontend_url: str | None = None) -> tuple[bool, str]:
    origin = frontend_url or settings.resolved_frontend_url
    reset_link = f"{origin}/reset-password?token={reset_token}"
    subject = "Reset Your Password - Testcase Executor.AI"
    year = datetime.now().year
    html_body = f"""\
<html>
<body style="font-family: Arial, sans-serif; background: #f4f4f5; padding: 20px;">
  <table width="100%" cellpadding="0" cellspacing="0">
    <tr>
      <td align="center">
        <table width="480" cellpadding="0" cellspacing="0" style="background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
          <tr>
            <td style="background: #4f46e5; padding: 32px 40px; text-align: center;">
              <h1 style="color: #ffffff; margin: 0; font-size: 22px;">Testcase Executor.AI</h1>
              <p style="color: #c7d2fe; margin: 8px 0 0 0; font-size: 13px;">Password Reset Request</p>
            </td>
          </tr>
          <tr>
            <td style="padding: 40px;">
              <p style="color: #334155; font-size: 15px; line-height: 1.6; margin: 0 0 20px 0;">
                You requested a password reset for your account. Click the button below to set a new password:
              </p>
              <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  <td align="center">
                    <a href="{reset_link}" style="display: inline-block; background: #4f46e5; color: #ffffff; text-decoration: none; padding: 14px 36px; border-radius: 8px; font-size: 15px; font-weight: 600;">Reset Password</a>
                  </td>
                </tr>
              </table>
              <p style="color: #64748b; font-size: 13px; line-height: 1.5; margin: 24px 0 0 0;">
                This link expires in 1 hour. If you didn't request this, you can safely ignore this email.
              </p>
            </td>
          </tr>
          <tr>
            <td style="background: #f8fafc; padding: 20px 40px; text-align: center;">
              <p style="color: #94a3b8; font-size: 12px; margin: 0;">&copy; {year} Testcase Executor.AI</p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""
    return await send_email(to_email, subject, html_body)
