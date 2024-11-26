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

from enum import StrEnum
from typing import Any
from urllib.parse import urlencode, urljoin

from django.conf import settings

from base.front.exceptions import InvalidFrontUrl


class Urls(StrEnum):
    PROJECT_HOME = "/project/{project_id}"
    PROJECT_INVITATION = "/accept-project-invitation/{invitation_token}"
    PROJECT_INVITATION_PREVIEW = "/project/{project_id}/preview/{invitation_token}"
    RESET_PASSWORD = "/reset-password/{reset_password_token}"
    VERIFY_SIGNUP = "/signup/verify/{verification_token}"
    WORKSPACE_INVITATION = "/accept-workspace-invitation/{invitation_token}"


def resolve_front_url(
    url_key: str, query_params: dict[str, str] | None = None, **kwargs: Any
) -> str:
    try:
        url_pattern = Urls[url_key]
    except KeyError:
        raise InvalidFrontUrl(f"Theres no front-end url matching the key `{url_key}`")

    url = urljoin(str(settings.FRONTEND_URL), str(url_pattern.value.format(**kwargs)))

    if query_params:
        return f"{url}?{urlencode(query_params)}"

    return url
