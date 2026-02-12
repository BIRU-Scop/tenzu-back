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

from enum import Enum

from django.conf import settings


class Emails(Enum):
    PROJECT_INVITATION = "project_invitation"
    RESET_PASSWORD = "reset_password"
    SIGN_UP = "sign_up"
    WORKSPACE_INVITATION = "workspace_invitation"


class EmailPart(Enum):
    TXT = "txt"
    HTML = "html"
    SUBJECT = "subject"


extra_email_context = {"settings": settings}
