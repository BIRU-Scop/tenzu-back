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

from urllib.parse import urljoin

from django.conf import settings
from pydantic import Field, field_validator

from commons.validators import BaseModel, check_not_empty


class ProviderRedirectValidator(BaseModel):
    callback_url: str = Field(
        description="The URL relative to the frontend to return to after the redirect flow is complete."
    )
    accept_terms_of_service: bool = False
    accept_privacy_policy: bool = False
    project_invitation_token: str | None = None
    accept_project_invitation: bool = True
    workspace_invitation_token: str | None = None
    accept_workspace_invitation: bool = True

    @field_validator("callback_url", mode="after")
    @classmethod
    def join_with_frontend(cls, value: str) -> str:
        check_not_empty(value)
        if not value.startswith("/"):
            raise ValueError("value must be a path starting with '/")
        return urljoin(str(settings.FRONTEND_URL), value)
