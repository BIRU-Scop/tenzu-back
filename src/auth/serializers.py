# Copyright (C) 2025 BIRU
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

from pydantic import ConfigDict

from base.serializers import BaseModel


class SocialProvider(BaseModel):
    id: str
    name: str
    client_id: str | None = None


class SocialAccountNestedSerializer(BaseModel):
    providers: list[SocialProvider]


class AuthConfigSerializer(BaseModel):
    socialaccount: SocialAccountNestedSerializer
    model_config = ConfigDict(from_attributes=True)


class AuthSocialSignupError(BaseModel):
    error: str
    error_process: str
    social_session_key: str | None = None
    email: str | None = None
