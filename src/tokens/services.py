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

from datetime import datetime

from base.db.models import Model
from tokens import repositories as tokens_repositories
from tokens.models import DenylistedToken, OutstandingToken

###########################################
# Outstanding Token
###########################################


async def create_outstanding_token(
    obj: Model,
    jti: str,
    token_type: str,
    token: str,
    created_at: datetime,
    expires_at: datetime,
) -> OutstandingToken:
    return await tokens_repositories.create_outstanding_token(
        obj=obj,
        jti=jti,
        token_type=token_type,
        token=token,
        created_at=created_at,
        expires_at=expires_at,
    )


async def update_or_create_outstanding_token(
    obj: Model,
    jti: str,
    token_type: str,
    token: str,
    created_at: datetime,
    expires_at: datetime,
) -> tuple[OutstandingToken, bool]:
    return await tokens_repositories.update_or_create_outstanding_token(
        obj=obj,
        jti=jti,
        token_type=token_type,
        token=token,
        created_at=created_at,
        expires_at=expires_at,
    )


async def get_or_create_outstanding_token(
    jti: str, token_type: str, token: str, expires_at: datetime
) -> tuple[OutstandingToken, bool]:
    return await tokens_repositories.get_or_create_outstanding_token(
        jti=jti, token_type=token_type, token=token, expires_at=expires_at
    )


async def outstanding_token_exist(jti: str) -> bool:
    return await tokens_repositories.outstanding_token_exist(jti=jti)


###########################################
# Denylisted Token
###########################################


async def deny_token(token: OutstandingToken) -> tuple[DenylistedToken, bool]:
    return await tokens_repositories.get_or_create_denylisted_token(token=token)


async def token_is_denied(jti: str) -> bool:
    return await tokens_repositories.denylisted_token_exist(jti=jti)


###########################################
# clean_expired_tokens
###########################################


async def clean_expired_tokens() -> None:
    await tokens_repositories.clean_expired_tokens()
