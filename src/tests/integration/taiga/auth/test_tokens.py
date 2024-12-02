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

import pytest
from asgiref.sync import sync_to_async

from auth.tokens import RefreshToken
from tests.utils import factories as f

pytestmark = pytest.mark.django_db


async def test_refresh_token_regenerate() -> None:
    # This test proves that it is possible to generate a refresh token from an existing one
    # and continue to use it without problems, postponing the creation of the OutstandingToken.
    user = await f.create_user(is_active=True)
    token = await sync_to_async(RefreshToken.for_user)(user)
    await token.blacklist()

    token1 = token.regenerate()
    token1_copy = await RefreshToken.create(token=str(token1))
    assert str(token1) == str(token1_copy)

    await token1.blacklist()
    token2 = token1.regenerate()

    token2_copy = await RefreshToken.create(token=str(token2))
    assert str(token2) == str(token2_copy)
