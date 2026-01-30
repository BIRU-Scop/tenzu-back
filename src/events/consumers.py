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
import asyncio
import json
import logging
from functools import cached_property
from typing import Any
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.conf import settings
from pycrdt import Doc, TransactionEvent, create_update_message
from pycrdt.websocket.django_channels_consumer import YjsConsumer
from pydantic import ValidationError

from base.utils.uuid import decode_b64str_to_uuid
from commons.exceptions.api import ForbiddenError
from events.actions import Action, ActionResponse, SystemResponse, channel_login
from permissions import check_permissions
from stories.stories.models import Story
from stories.stories.permissions import StoryPermissionsCheck

event_logger = logging.getLogger("events.consumers.event")
collaboration_logger = logging.getLogger("events.consumers.collaboration")


class EventConsumer(AsyncJsonWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._subscribed_channels: set[str] = set()

    async def connect(self):
        from django.contrib.auth.models import AnonymousUser

        self.scope["user"] = AnonymousUser()
        event_logger.debug("Connected")
        await self.accept()

    async def receive_json(self, content, **kwargs):
        try:
            action = Action(action=content)

            event_logger.debug(f"Received action {content['command']}")
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
        if self._subscribed_channels:
            event_logger.debug(
                f"Unsubscribing from {len(self._subscribed_channels)} channel(s): "
                f"{', '.join(sorted(self._subscribed_channels))}"
            )
            await asyncio.gather(
                *[
                    self.channel_layer.group_discard(channel, self.channel_name)
                    for channel in self._subscribed_channels
                ],
                return_exceptions=True,
            )
            self._subscribed_channels.clear()
        event_logger.debug(f"Disconnected : code {close_code}")

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
        self._subscribed_channels.add(channel)

    async def unsubscribe(self, channel: str):
        await self.channel_layer.group_discard(channel, self.channel_name)
        self._subscribed_channels.discard(channel)

    async def emit_event(self, event):
        await self.send_json(event["event"])


class CollaborationConsumer(YjsConsumer):
    """
    WebSocket consumer for collaborative document editing using Yjs CRDT.
    Handles real-time synchronization and debounced persistence to the database.
    """

    # Lifecycle methods
    def __init__(self):
        super().__init__()
        self.story = None
        self._save_task = None

    async def connect(self):
        """
        Handles WebSocket connection establishment.
        Authenticates the user via token and initializes the Yjs document.
        """
        try:
            user = await self.authenticate_connection()
            self.scope["user"] = user
            await super().connect()

        except Exception as e:
            collaboration_logger.error(
                f"Connection failed for user: {e}", exc_info=True
            )
            await self.close(code=4000)
        finally:
            collaboration_logger.debug(
                f"connected {self.project_uuid}/{self.story_ref}"
            )

    async def disconnect(self, close_code):
        """
        Called when the WebSocket connection is closed.
        Ensures any pending changes are saved before disconnection.
        """
        try:
            if self._save_task:
                self._save_task.cancel()
                await self.force_save()
        except Exception as e:
            collaboration_logger.error(f"Failed final save: {e}")
        finally:
            collaboration_logger.debug(
                f"Collaboration disconnected {self.project_uuid}/{self.story_ref}"
            )
            await super().disconnect(close_code)

    async def receive(self, text_data=None, bytes_data=None):
        """
        Handles incoming WebSocket messages.
        Intercepts manual save commands before delegating to YjsConsumer for binary data.
        """
        if text_data:
            try:
                data = json.loads(text_data)
                if data.get("command") == "save_now":
                    collaboration_logger.debug("Manual save requested by client")
                    await self.force_save()
                    await self.send(
                        text_data=json.dumps({"type": "save_status", "status": "saved"})
                    )
                    return None
            except json.JSONDecodeError:
                pass

        return await super().receive(text_data, bytes_data)

    # YjsConsumer overrides
    def make_room_name(self) -> str:
        """
        Generates a unique room name for the collaborative editing session.
        Groups users editing the same story in the same project into one room.
        """
        return f"{self.project_uuid}-{self.story_ref}"

    async def make_ydoc(self) -> Doc:
        """
        Creates and initializes a Yjs document for collaborative editing.
        Loads existing document state from the database if available.
        """
        self.story = await Story.objects.only("description_binary").aget(
            ref=self.story_ref,
            project_id=self.project_uuid,
        )
        doc = Doc()
        if self.story.description_binary:
            doc.apply_update(self.story.description_binary)
        doc.observe(self.on_update_event)
        return doc

    async def doc_update(self, update_wrapper):
        """
        Receives document updates from other clients in the same room
        and broadcasts them to all connected clients.
        """
        update = update_wrapper["update"]
        self.ydoc.apply_update(update)
        await self.group_send_message(create_update_message(update))

    # Document update handlers
    def on_update_event(self, event: TransactionEvent):
        """
        Called whenever the Yjs document is updated.
        Schedules a debounced save operation.
        """
        loop = asyncio.get_event_loop()
        loop.call_soon_threadsafe(self.schedule_save)

    def schedule_save(self):
        """
        Cancels any existing save task and schedules a new debounced save.
        This implements a debouncing pattern to avoid saving on every keystroke.
        """
        if self._save_task:
            self._save_task.cancel()
        self._save_task = asyncio.create_task(self.debounced_save())

    # Save operations
    async def debounced_save(self):
        """
        Waits for a period of inactivity before saving the document to the database.
        This reduces the number of database writes during active editing.
        """
        try:
            await asyncio.sleep(settings.EVENTS_DEBOUNCE_SAVE_DELAY)
            await self._save_to_db()
            self._save_task = None
        except asyncio.CancelledError:
            # Task was cancelled (e.g., new update came in), which is expected behavior
            pass

    async def force_save(self):
        """
        Performs an immediate save to the database, bypassing the debounce timer.
        Cancels any pending debounced save tasks.
        """
        if self._save_task:
            self._save_task.cancel()
            self._save_task = None
        await self._save_to_db()

    async def _save_to_db(self):
        """
        Internal method that performs the actual database save operation.
        """
        update = self.ydoc.get_update()
        await Story.objects.filter(
            ref=self.story_ref, project_id=self.project_uuid
        ).aupdate(description_binary=update)

    # Helper methods
    async def authenticate_connection(self):
        """
        Extracts and validates the authentication token from the query string.
        """
        query_params = parse_qs(self.scope.get("query_string", b"").decode("utf-8"))
        token = query_params.get("token", [None])[0]
        if not token:
            raise ValueError("Missing authentication token")
        return await database_sync_to_async(channel_login)(token)

    @cached_property
    def project_uuid(self):
        """Returns the decoded project UUID from the URL route."""
        return decode_b64str_to_uuid(self.scope["url_route"]["kwargs"]["project_id"])

    @property
    def story_ref(self):
        """Returns the story reference from the URL route."""
        return self.scope["url_route"]["kwargs"]["story_ref"]
