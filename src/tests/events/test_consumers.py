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

from events import channels
from tests.utils import factories as f
from tests.utils.events import build_consumer

SIGNOUT_RESPONSE = {"type": "action", "status": "ok", "action": {"command": "signout"}}


async def test_unsubscribe_all_discards_every_channel_from_the_channel_layer():
    user = f.build_user()
    consumer = await build_consumer(
        user=user, subscribed={channels.user_channel(user), "projects.p1"}
    )

    await consumer.unsubscribe_all()

    assert consumer.channel_layer.groups == {}


async def test_send_action_response_unsubscribes_every_channel_when_the_action_is_signout():
    user = f.build_user()
    consumer = await build_consumer(
        user=user, subscribed={channels.user_channel(user), "projects.p1"}
    )

    await consumer.send_action_response(
        {"data": SIGNOUT_RESPONSE, "sender_channel_name": "another-consumer"}
    )

    assert consumer._subscribed_channels == set()


async def test_send_action_response_sets_the_scope_user_to_anonymous_when_the_action_is_signout():
    user = f.build_user()
    consumer = await build_consumer(user=user, subscribed={channels.user_channel(user)})

    await consumer.send_action_response(
        {"data": SIGNOUT_RESPONSE, "sender_channel_name": "another-consumer"}
    )

    assert not consumer.scope["user"].is_authenticated


async def test_send_action_response_sends_the_signout_response_when_the_sender_is_another_consumer():
    user = f.build_user()
    consumer = await build_consumer(user=user, subscribed={channels.user_channel(user)})

    await consumer.send_action_response(
        {"data": SIGNOUT_RESPONSE, "sender_channel_name": "another-consumer"}
    )

    assert consumer.sent == [SIGNOUT_RESPONSE]


async def test_send_action_response_sends_nothing_when_the_sender_is_this_consumer():
    user = f.build_user()
    consumer = await build_consumer(user=user, subscribed={channels.user_channel(user)})

    await consumer.send_action_response(
        {"data": SIGNOUT_RESPONSE, "sender_channel_name": consumer.channel_name}
    )

    assert consumer.sent == []


async def test_send_action_response_sends_the_signin_response_to_its_sender():
    user = f.build_user()
    consumer = await build_consumer(user=user, subscribed=set())
    signin_response = {
        "type": "action",
        "status": "ok",
        "action": {"command": "signin"},
        "content": {"channel": channels.user_channel(user)},
    }

    await consumer.send_action_response(
        {"data": signin_response, "sender_channel_name": consumer.channel_name}
    )

    assert consumer.sent == [signin_response]
