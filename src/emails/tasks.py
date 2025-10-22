# -*- coding: utf-8 -*-
# Copyright (C) 2024-2025 BIRU
#
# This file is part of Tenzu.
#
# Tenzu is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
#
# You can contact BIRU at ask@biru.sh

import logging
from typing import Any

from aiosmtplib import SMTPConnectError
from django.conf import settings
from jinja2 import TemplateNotFound
from procrastinate import RetryStrategy
from procrastinate.contrib.django import app

from base.i18n import i18n
from emails import exceptions as ex
from emails.emails import Emails
from emails.render import render_email_html, render_email_txt, render_subject
from emails.sender import send_email_message

logger = logging.getLogger(__name__)


@app.task(
    retry=RetryStrategy(
        max_attempts=settings.EMAIL_RETRY_ATTEMPTS,
        exponential_wait=settings.EMAIL_RETRY_EXPONENTIAL_WAIT,
        retry_exceptions={ex.EmailSMTPError, ex.EmailDeliveryError},
    )
)
async def send_email(
    email_name: str,
    to: str | list[str],
    context: dict[str, Any] = {},
    attachment_paths: list[str] = [],
    lang: str = settings.LANGUAGE_CODE,
) -> None:
    # validate the email template
    try:
        Emails(email_name)
    except ValueError:
        raise ex.EmailTemplateError(
            f"The email `{email_name}` it's not an allowed `Emails` instance"
        )

    # prepare the email recipients
    to_emails = to
    if isinstance(to_emails, str):
        to_emails = [to_emails]
    if not to_emails:
        logger.error("Requested to send an email with no recipients. Aborting.")
        return

    # render the email contents in the user's language using both the email template and variables dictionary
    with i18n.use(lang):
        try:
            body_txt = render_email_txt(email_name, context)
            subject = render_subject(email_name, context)
            body_html = render_email_html(email_name, context)
        except TemplateNotFound as template_exception:
            raise ex.EmailTemplateError(
                f"Missing or invalid email template. {template_exception}"
            )

    # send the email message using the configured backend
    try:
        await send_email_message(
            subject=subject,
            to_emails=to_emails,
            body_txt=body_txt,
            body_html=body_html,
            attachment_paths=attachment_paths,
        )
    except SMTPConnectError as smtp_exception:
        raise ex.EmailSMTPError(
            f"SMTP connection could not be established. {smtp_exception}"
        )
    except FileNotFoundError as file_attachments_exception:
        raise ex.EmailAttachmentError(
            f"Email attachment error. {file_attachments_exception}"
        )
    except Exception as delivery_exception:
        raise ex.EmailDeliveryError(
            f"Unknown error while delivering an email. {delivery_exception}"
        )
