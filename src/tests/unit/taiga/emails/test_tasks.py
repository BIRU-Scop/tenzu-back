# -*- coding: utf-8 -*-
# Copyright (C) 2024-2026 BIRU
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

import tempfile
from smtplib import SMTPConnectError
from unittest.mock import patch

import pytest
from conf.emails import EmailBackends
from fastapi_mailman import Mail
from fastapi_mailman.config import ConnectionConfig

from emails.exceptions import (
    EmailAttachmentError,
    EmailDeliveryError,
    EmailSMTPError,
    EmailTemplateError,
)
from emails.tasks import send_email

SUBJECT = "Email sent from FastPI-Mailman"
TO_EMAILS = ["username1@domain.name", "username2@domain.name"]
BODY_TXT = "This is the Text message"
BODY_HTML = (
    "<h1>Hello User</h1><h2>One</h2><ul><li>Foo</li><li>Bar</li><li>Qux</li></ul>"
)
EMAIL_NAME = "sign_up"
CONTEXT = {
    "verify_url": "https://testing.domain.com/verify-email/396438bb-894a-4401-8d3b-7c0d22abaf5b",
    "support_email": "support@testing.domain",
}
RENDERED_EMAIL_TXT = "rendered email txt"

email_config = ConnectionConfig(
    MAIL_BACKEND=EmailBackends.DUMMY.value,
    MAIL_DEFAULT_SENDER="username@domain.name",
    MAIL_SERVER="testing.smtp.com",
    MAIL_USERNAME="username",
    MAIL_PASSWORD="password",
)
dummy_email_connection = Mail(email_config).get_connection()


async def test_send_email_ok_all_params():
    with (
        patch(
            "emails.tasks.send_email_message", autospec=True
        ) as fake_send_email_message,
        patch("emails.tasks.render_email_txt", return_value=BODY_TXT),
        patch("emails.tasks.render_email_html", return_value=BODY_HTML),
        patch("emails.tasks.render_subject", return_value=SUBJECT),
        tempfile.NamedTemporaryFile(mode="wb") as jpg,
        tempfile.NamedTemporaryFile(mode="wb") as txt,
    ):
        await send_email(
            email_name=EMAIL_NAME,
            context=CONTEXT,
            to=TO_EMAILS,
            attachment_paths=[txt.name, jpg.name],
        )

        fake_send_email_message.assert_called_once_with(
            subject=SUBJECT,
            to_emails=TO_EMAILS,
            body_txt=BODY_TXT,
            body_html=BODY_HTML,
            attachment_paths=[txt.name, jpg.name],
        )


async def test_send_email_ok_single_recipient():
    with (
        patch(
            "emails.tasks.send_email_message", autospec=True
        ) as fake_send_email_message,
        patch("emails.tasks.render_email_txt", return_value=BODY_TXT),
        patch("emails.tasks.render_email_html", return_value=BODY_HTML),
        patch("emails.tasks.render_subject", return_value=SUBJECT),
    ):
        await send_email(email_name=EMAIL_NAME, context=CONTEXT, to=TO_EMAILS[0])

        fake_send_email_message.assert_called_once_with(
            subject=SUBJECT,
            to_emails=[TO_EMAILS[0]],
            body_txt=BODY_TXT,
            body_html=BODY_HTML,
            attachment_paths=[],
        )


async def test_send_email_no_recipients():
    with patch(
        "emails.tasks.send_email_message", autospec=True
    ) as fake_send_email_message:
        await send_email(email_name=EMAIL_NAME, context=CONTEXT, to=TO_EMAILS[0])

        assert not fake_send_email_message.assert_awaited()


async def test_send_email_wrong_template():
    with (
        patch("emails.tasks.send_email_message", autospec=True),
        pytest.raises(EmailTemplateError),
    ):
        await send_email(
            email_name="not_a_valid_email_template", context=CONTEXT, to=TO_EMAILS[0]
        )


async def test_send_email_wrong_attachments():
    with (
        patch(
            "emails.tasks.send_email_message",
            autospec=True,
            side_effect=FileNotFoundError(),
        ),
        pytest.raises(EmailAttachmentError),
    ):
        await send_email(
            email_name=EMAIL_NAME,
            context=CONTEXT,
            to=TO_EMAILS,
            attachment_paths=["/bad/file_path.txt"],
        )


async def test_send_email_smtp_error():
    with (
        patch(
            "emails.tasks.send_email_message",
            autospec=True,
            side_effect=SMTPConnectError(""),
        ),
        pytest.raises(EmailSMTPError),
    ):
        await send_email(email_name=EMAIL_NAME, context=CONTEXT, to=TO_EMAILS)


async def test_send_email_unknown_error():
    with (
        patch(
            "emails.tasks.send_email_message", autospec=True, side_effect=Exception()
        ),
        pytest.raises(EmailDeliveryError),
    ):
        await send_email(email_name=EMAIL_NAME, context=CONTEXT, to=TO_EMAILS)
