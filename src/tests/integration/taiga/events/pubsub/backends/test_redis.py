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

import logging

import pytest

from events.events import Event
from events.pubsub.backends.exceptions import PubSubBackendIsNotConnected
from events.pubsub.backends.redis import RedisPubSubBackend


@pytest.fixture
async def pubsub() -> RedisPubSubBackend:
    pubsub = RedisPubSubBackend(host="localhost", port=6379, db=0)
    yield pubsub

    if pubsub.is_connected:
        await pubsub.disconnect()


async def test_connect(pubsub):
    assert not pubsub.is_connected
    await pubsub.connect()
    assert pubsub.is_connected


async def test_disconnect(pubsub):
    await pubsub.connect()
    assert pubsub.is_connected
    await pubsub.disconnect()
    assert not pubsub.is_connected


async def test_method_who_need_connection(pubsub):
    channel = "test_ch"
    event = Event(type="test", content={"msg": "msg"})

    assert not pubsub.is_connected

    with pytest.raises(PubSubBackendIsNotConnected):
        await pubsub.disconnect()
    with pytest.raises(PubSubBackendIsNotConnected):
        await pubsub.subscribe(channel)
    with pytest.raises(PubSubBackendIsNotConnected):
        await pubsub.unsubscribe(channel)
    with pytest.raises(PubSubBackendIsNotConnected):
        await pubsub.publish(channel, event)
    with pytest.raises(PubSubBackendIsNotConnected):
        await pubsub.next_published()


async def test_subscribe(pubsub):
    channel = "test_ch_1"
    await pubsub.connect()
    assert channel.encode() not in pubsub._pubsub.channels
    await pubsub.subscribe(channel)
    assert channel.encode() in pubsub._pubsub.channels


async def test_subscribe_to_channel_with_a_long_name(pubsub):
    channel = "test_ch_1" * 255
    await pubsub.connect()
    assert channel.encode() not in pubsub._pubsub.channels
    await pubsub.subscribe(channel)
    assert channel.encode() in pubsub._pubsub.channels


async def test_unsubscribe(pubsub):
    channel = "test_ch_1"
    await pubsub.connect()
    await pubsub.subscribe(channel)
    assert channel.encode() not in pubsub._pubsub.pending_unsubscribe_channels
    await pubsub.unsubscribe(channel)
    assert channel.encode() in pubsub._pubsub.pending_unsubscribe_channels


async def test_publish_and_listen(pubsub):
    channel1 = "test_ch_1"
    channel2 = "test_ch_2"
    event1 = Event(type="test", content={"msg": "msg1"})
    event2 = Event(type="test", content={"msg": "msg2"})

    await pubsub.connect()
    await pubsub.subscribe(channel1)
    # publish
    await pubsub.publish(channel1, event1)
    await pubsub.publish(channel2, event1)
    await pubsub.publish(channel1, event2)
    # listen
    assert (channel1, event1) == await pubsub.next_published()
    assert (channel1, event2) == await pubsub.next_published()
    # publish invalid event
    await pubsub.publish(channel1, "INVALID EVENT")
    await pubsub.publish(channel1, "INVALID EVENT")


async def test_publish_invalid_events_and_listen(pubsub, caplog):
    with caplog.at_level(logging.NOTSET, logger="events.pubsub.backends.postgres"):
        channel = "test_ch"
        event1 = Event(type="test", content={"msg": "msg1"})
        event2 = Event(type="test", content={"msg": "msg2"})

        await pubsub.connect()
        await pubsub.subscribe(channel)
        # publish
        await pubsub.publish(channel, event1)
        # await pubsub.publish(channel, "INVALID EVENT")
        await pubsub.publish(channel, event2)
        # listen
        assert (channel, event1) == await pubsub.next_published()
        assert (channel, event2) == await pubsub.next_published()
