from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

from config.config_loader import settings


logger = logging.getLogger(__name__)


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

    stage = "connect"

    try:
        if encryption == "ssl":
            smtp = smtplib.SMTP_SSL(settings.APP_SMTP_HOST, settings.APP_SMTP_PORT, timeout=20)
        else:
            smtp = smtplib.SMTP(settings.APP_SMTP_HOST, settings.APP_SMTP_PORT, timeout=20)

        with smtp:
            stage = "EHLO"
            smtp.ehlo()

            if encryption in {"tls", "starttls"}:
                stage = "STARTTLS"
                smtp.starttls()
                stage = "EHLO after STARTTLS"
                smtp.ehlo()

            if settings.APP_SMTP_USERNAME and settings.APP_SMTP_PASSWORD:
                stage = "authentication"
                smtp.login(settings.APP_SMTP_USERNAME, settings.APP_SMTP_PASSWORD)

            stage = "message delivery"
            smtp.send_message(message)
    except (OSError, smtplib.SMTPException) as exc:
        logger.exception(
            "SMTP email failed during %s via %s:%s with encryption=%s",
            stage,
            settings.APP_SMTP_HOST,
            settings.APP_SMTP_PORT,
            encryption or "none",
        )
        raise MailerDeliveryError("Unable to send email") from exc
