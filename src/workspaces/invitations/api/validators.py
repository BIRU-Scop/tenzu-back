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

from typing import List, Set

from django.conf import settings
from pydantic import Field, field_validator
from typing_extensions import Annotated

from base.utils.emails import is_email
from base.validators import BaseModel, StrNotEmpty


class WorkspaceInvitationValidator(BaseModel):
    username_or_email: StrNotEmpty

    @field_validator("username_or_email")
    @classmethod
    def check_email_in_domain(cls, v: str) -> str:
        if is_email(value=v):
            if not settings.USER_EMAIL_ALLOWED_DOMAINS:
                return v

            domain = v.split("@")[1]
            assert (
                domain in settings.USER_EMAIL_ALLOWED_DOMAINS
            ), "Email domain not allowed"
        return v


class WorkspaceInvitationsValidator(BaseModel):
    # Max items 50 and duplicated items not allowed
    invitations: Annotated[List[WorkspaceInvitationValidator], Field(max_length=50)]
