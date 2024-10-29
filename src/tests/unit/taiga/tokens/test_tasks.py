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

from unittest.mock import patch

from tokens import tasks

##########################################################
# clean_expired_tokens
##########################################################


async def test_clean_expired_tokens():
    with patch("tokens.tasks.tokens_services", autospec=True) as fake_tokens_services:
        await tasks.clean_expired_tokens(0)
        fake_tokens_services.clean_expired_tokens.assert_awaited_once()
