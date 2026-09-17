from __future__ import annotations

import smtplib
from email.message import EmailMessage

from config.config_loader import settings


class MailerConfigurationError(RuntimeError):
    pass


class MailerDeliveryError(RuntimeError):
    pass


def send_email(to_email: str, subject: str, text_body: str, html_body: str | None = None) -> None:
    if not settings.APP_SMTP_HOST or not settings.APP_MAIL_FROM:
        raise MailerConfigurationError("SMTP host and sender address must be configured")

    message = EmailMessage()
    message["From"] = settings.APP_MAIL_FROM
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(text_body)

    if html_body:
        message.add_alternative(html_body, subtype="html")

    encryption = (settings.APP_SMTP_ENCRYPTION or "").strip().lower()

    try:
        if encryption == "ssl":
            smtp = smtplib.SMTP_SSL(settings.APP_SMTP_HOST, settings.APP_SMTP_PORT, timeout=20)
        else:
            smtp = smtplib.SMTP(settings.APP_SMTP_HOST, settings.APP_SMTP_PORT, timeout=20)

        with smtp:
            if encryption in {"tls", "starttls"}:
                smtp.starttls()

            if settings.APP_SMTP_USERNAME and settings.APP_SMTP_PASSWORD:
                smtp.login(settings.APP_SMTP_USERNAME, settings.APP_SMTP_PASSWORD)

            smtp.send_message(message)
    except (OSError, smtplib.SMTPException) as exc:
        raise MailerDeliveryError("Unable to send email") from exc
