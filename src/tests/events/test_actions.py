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

from unittest.mock import patch

import pytest

from events import channels
from events.actions import ActionResponse, SignInAction, SignOutLocalAction
from tests.utils import factories as f
from tests.utils.events import build_consumer


@pytest.mark.django_db
async def test_signin_unsubscribes_the_channels_of_the_previous_user():
    previous_user = f.build_user()
    next_user = f.build_user()
    consumer = await build_consumer(
        user=previous_user,
        subscribed={channels.user_channel(previous_user), "projects.p1"},
    )

    with patch("events.actions.channel_login", autospec=True, return_value=next_user):
        await SignInAction(token="token-for-next-user").run(consumer)

    assert consumer._subscribed_channels == {channels.user_channel(next_user)}


@pytest.mark.django_db
async def test_signin_keeps_the_channels_when_the_user_is_unchanged():
    user = f.build_user()
    consumer = await build_consumer(
        user=user, subscribed={channels.user_channel(user), "projects.p1"}
    )

    with patch("events.actions.channel_login", autospec=True, return_value=user):
        await SignInAction(token="token-for-the-same-user").run(consumer)

    assert consumer._subscribed_channels == {channels.user_channel(user), "projects.p1"}


async def test_signout_local_unsubscribes_every_channel():
    user = f.build_user()
    consumer = await build_consumer(
        user=user, subscribed={channels.user_channel(user), "projects.p1"}
    )

    await SignOutLocalAction().run(consumer)

    assert consumer._subscribed_channels == set()


async def test_signout_local_sets_the_scope_user_to_anonymous():
    user = f.build_user()
    consumer = await build_consumer(user=user, subscribed={channels.user_channel(user)})

    await SignOutLocalAction().run(consumer)

    assert not consumer.scope["user"].is_authenticated


async def test_signout_local_broadcasts_nothing():
    user = f.build_user()
    consumer = await build_consumer(user=user, subscribed={channels.user_channel(user)})

    await SignOutLocalAction().run(consumer)

    assert consumer.channel_layer.channels == {}


async def test_signout_local_sends_not_signed_in_when_the_consumer_is_anonymous():
    consumer = await build_consumer()

    await SignOutLocalAction().run(consumer)

    assert consumer.sent == [
        ActionResponse(
            action=SignOutLocalAction(),
            status="error",
            content={"detail": "not-signed-in"},
        ).model_dump()
    ]
