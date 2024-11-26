# -*- coding: utf-8 -*-
# Copyright (C) 2024 BIRU
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

from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection
from django.core.mail.backends.base import BaseEmailBackend


async def send_email_message(
    subject: str | None = None,
    to_emails: list[str] = [],
    from_email: str | None = None,
    body_txt: str | None = None,
    body_html: str | None = None,
    attachment_paths: list[str] = [],
) -> None:
    """
    NOTE: DO NOT USE THIS SERVICE DIRECTLY, USE THE TASK INSTEAD

    Send multipart (attachments) / alternative (text and HTML version) messages
    to multiple recipients using the configured backend
    """

    message = EmailMultiAlternatives(
        connection=_get_mail_connection(),
        subject=subject,
        body=body_txt,
        to=to_emails,
        from_email=from_email,
    )

    if body_html:
        message.attach_alternative(body_html, "text/html")

    for attachment_path in attachment_paths:
        message.attach_file(path=attachment_path)

    message.send()


def _get_mail_connection() -> BaseEmailBackend:
    return get_connection(backend=settings.EMAIL_BACKEND)
