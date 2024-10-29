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
from channels.layers import get_channel_layer

from events import channels
from events.actions import EventResponse
from events.events import Event, EventContent
from projects.projects.models import Project
from users.models import AnyUser
from workspaces.workspaces.models import Workspace


class EventsManager:
    def __init__(self):
        self.channel_layer = get_channel_layer()

    async def publish(self, channel: str, event: Event) -> None:
        event = EventResponse(channel=channel, event=event)
        await self.channel_layer.send(
            channel,
            {
                "type": "emit.event",
                "event": event.model_dump(by_alias=True, mode="json"),
            },
        )

    def _generate_event(self, type: str, content: EventContent = None) -> Event:
        return Event(
            type=type,
            content=content.model_dump(by_alias=True) if content else None,
        )

    async def publish_on_system_channel(self, type: str, content: EventContent) -> None:
        channel = channels.system_channel()
        event = self._generate_event(type=type, content=content)
        await self.publish(channel=channel, event=event)

    async def publish_on_user_channel(self, user: AnyUser | str, type: str, content: EventContent = None) -> None:
        channel = channels.user_channel(user)
        event = self._generate_event(type=type, content=content)
        await self.publish(channel=channel, event=event)

    async def publish_on_project_channel(self, project: Project | str, type: str, content: EventContent = None) -> None:
        channel = channels.project_channel(project)
        event = self._generate_event(type=type, content=content)
        await self.publish(channel=channel, event=event)

    async def publish_on_workspace_channel(
        self,
        workspace: Workspace | str,
        type: str,
        content: EventContent = None,
    ) -> None:
        channel = channels.workspace_channel(workspace)
        event = self._generate_event(type=type, content=content)
        await self.publish(channel=channel, event=event)


manager = EventsManager()
