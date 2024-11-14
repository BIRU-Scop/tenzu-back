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
from typing import Any

from channels.generic.websocket import AsyncJsonWebsocketConsumer
from pydantic import ValidationError

from events.actions import Action, ActionResponse, SystemResponse

logger = logging.getLogger("django")


class EventConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        from django.contrib.auth.models import AnonymousUser

        self.scope["user"] = AnonymousUser()
        await self.accept()

    async def receive_json(self, content, **kwargs):
        try:
            action = Action(action=content)
            await action.action.run(self)
        except ValidationError as e:
            await self.emit_event(
                {
                    "event": SystemResponse(
                        status="error",
                        content={"detail": "invalid-action", "error": e.errors()},
                    ).model_dump()
                }
            )

    async def disconnect(self, close_code):
        pass

    async def broadcast_action_response(self, channel: str, action: ActionResponse):
        """
        use this to broadcast a action response
        """
        await self.channel_layer.group_send(
            channel, {"type": "send_action_response", "data": action.model_dump()}
        )

    async def send_action_response(self, action: dict[str, Any]):
        await self.send_json(action["data"])

    async def send_without_broadcast_action_response(self, action: dict[str, Any]):
        await self.send_json(action)

    async def subscribe(self, channel: str):
        await self.channel_layer.group_add(channel, self.channel_name)

    async def unsubscribe(self, channel: str):
        await self.channel_layer.group_discard(channel, self.channel_name)

    async def emit_event(self, event):
        await self.send_json(event["event"])
