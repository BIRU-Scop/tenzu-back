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
from pydantic import ValidationError

from events.actions import PingAction, SignInAction, parse_action_from_text


def test_parse_action_from_text_discover_action_type():
    action_ping = parse_action_from_text("""{ "command": "ping" }""")
    action_signin = parse_action_from_text(
        """{ "command": "signin", "token": "sometoken" }"""
    )

    assert isinstance(action_ping, PingAction)
    assert isinstance(action_signin, SignInAction)


def test_parse_action_from_text_raise_validation_error():
    with pytest.raises(ValidationError) as e:
        parse_action_from_text("""{ "command": "pong" }""")
    assert e.value.errors()[0]["type"] == "value_error"

    with pytest.raises(ValidationError) as e:
        parse_action_from_text("""{ "command": "signin" }""")
    assert e.value.errors()[0]["type"] == "value_error.missing"
