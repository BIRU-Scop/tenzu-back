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

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ALLOWED_ALGORITHMS = (
    "HS256",
    "HS384",
    "HS512",
    "RS256",
    "RS384",
    "RS512",
)


class TokensSettings(BaseSettings):
    ALGORITHM: str = "HS256"
    SIGNING_KEY: str = ""
    VERIFYING_KEY: str = ""
    AUDIENCE: str | None = None
    ISSUER: str | None = None

    TOKEN_TYPE_CLAIM: str = "token_type"
    JTI_CLAIM: str = "jti"

    # Validators
    @field_validator("ALGORITHM", mode="before")
    @classmethod
    def validate_algorithm(cls, v: str) -> str:
        if v not in ALLOWED_ALGORITHMS:
            raise ValueError(v)
        return v

    model_config = SettingsConfigDict(case_sensitive=True)
