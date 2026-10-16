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
from typing import Any
from unittest.mock import patch

import pytest
from channels.layers import get_channel_layer
from channels.testing import WebsocketCommunicator

from events import events_manager
from events.actions import ActionResponse, SignOutAction
from events.consumers import EventConsumer
from ninja_jwt.authentication import JWTBaseAuthentication
from ninja_jwt.tokens import AccessToken
from tests.utils import factories as f

USER_UPDATE_EVENT = "users.update"


async def open_signed_in_tab(token: str) -> WebsocketCommunicator:
    tab = WebsocketCommunicator(EventConsumer.as_asgi(), "/events/")
    await tab.connect()
    await tab.send_json_to({"command": "signin", "token": token})
    return tab


async def received_messages(tab: WebsocketCommunicator) -> list[dict[str, Any]]:
    messages = []
    while not await tab.receive_nothing():
        messages.append(await tab.receive_json_from())
    return messages


@pytest.fixture
def user():
    return f.build_user()


@pytest.fixture
async def signed_tabs(user):
    """Two signed-in tabs of the same user"""
    token = str(AccessToken.for_user(user))
    with patch.object(JWTBaseAuthentication, "get_user", return_value=user):
        tabs = [await open_signed_in_tab(token) for _ in range(2)]
        for tab in tabs:
            await received_messages(tab)
        yield tabs
        for tab in tabs:
            await tab.disconnect()
    await get_channel_layer().flush()


async def test_signin_subscribes_every_tab_of_the_user_to_the_user_channel(
    user, signed_tabs
):
    await events_manager.publish_on_user_channel(user, type=USER_UPDATE_EVENT)

    with patch.object(JWTBaseAuthentication, "get_user", return_value=user):
        assert [
            [message["event"]["type"] for message in await received_messages(tab)]
            for tab in signed_tabs
        ] == [[USER_UPDATE_EVENT], [USER_UPDATE_EVENT]]


async def test_signout_sends_the_signout_response_to_the_other_tabs_of_the_user(
    signed_tabs,
):
    sender, other = signed_tabs

    await sender.send_json_to({"command": "signout"})

    with patch.object(JWTBaseAuthentication, "get_user", return_value=user):
        assert await received_messages(other) == [
            ActionResponse(action=SignOutAction()).model_dump()
        ]


async def test_signout_sends_nothing_to_the_tab_that_sent_it(signed_tabs):
    sender, other = signed_tabs

    with patch.object(JWTBaseAuthentication, "get_user", return_value=user):
        await sender.send_json_to({"command": "signout"})
        await received_messages(other)

        assert await received_messages(sender) == []


async def test_signout_unsubscribes_every_tab_of_the_user_from_the_user_channel(
    user, signed_tabs
):
    sender, other = signed_tabs
    with patch.object(JWTBaseAuthentication, "get_user", return_value=user):
        await sender.send_json_to({"command": "signout"})
        await received_messages(other)

        await events_manager.publish_on_user_channel(user, type=USER_UPDATE_EVENT)

        assert [await received_messages(tab) for tab in signed_tabs] == [[], []]
