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

import pytest
from channels.layers import InMemoryChannelLayer
from django.contrib.auth.models import AbstractBaseUser, AnonymousUser

from events.consumers import EventConsumer


class RecordingEventConsumer(EventConsumer):
    """A real EventConsumer without a socket: what it sends is recorded instead."""

    channel_layer: InMemoryChannelLayer

    def __init__(self, user: AbstractBaseUser | AnonymousUser) -> None:
        super().__init__()
        self.scope = {"user": user}
        self.channel_layer = InMemoryChannelLayer()
        self.channel_name = "consumer-under-test"
        self.sent: list[Any] = []

    async def send_json(self, content: Any, close: bool = False) -> None:
        self.sent.append(content)


async def build_consumer(
    user: AbstractBaseUser | AnonymousUser | None = None,
    subscribed: set[str] | None = None,
) -> RecordingEventConsumer:
    consumer = RecordingEventConsumer(user=user or AnonymousUser())
    for channel in subscribed or set():
        await consumer.subscribe(channel)
    return consumer
