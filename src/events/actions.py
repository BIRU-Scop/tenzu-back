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
from typing import TYPE_CHECKING, Any, Literal, Union

from channels.db import database_sync_to_async
from django.contrib.auth.models import AbstractUser, AnonymousUser
from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field
from typing_extensions import Annotated

from base.api.permissions import check_permissions
from base.utils.uuid import decode_b64str_to_uuid
from events import channels
from events.events import Event
from exceptions.api import ForbiddenError
from ninja_jwt.authentication import JWTBaseAuthentication
from ninja_jwt.exceptions import AuthenticationFailed
from permissions import CanViewProject, HasPerm
from projects.projects.models import Project
from workspaces.workspaces.models import Workspace

if TYPE_CHECKING:
    from events.consumers import EventConsumer


def channel_login(token: str) -> AbstractUser:
    backend = JWTBaseAuthentication()
    token = JWTBaseAuthentication.get_validated_token(token)
    user = backend.get_user(token)
    return user


class SignInAction(PydanticBaseModel):
    command: Literal["signin"] = "signin"
    token: str

    async def run(self, consumer: "EventConsumer") -> None:
        try:
            user: AbstractUser = await database_sync_to_async(channel_login)(self.token)
            consumer.scope["user"] = user
            channel = channels.user_channel(user)
            await consumer.subscribe(channel)
            await consumer.send_action_response(ActionResponse(action=self, content={"channel": channel}))
        except AuthenticationFailed:
            await consumer.send_action_response(
                ActionResponse(
                    action=self,
                    status="error",
                    content={"detail": "invalid-credentials"},
                )
            )


class SignOutAction(PydanticBaseModel):
    command: Literal["signout"] = "signout"

    async def run(self, consumer: "EventConsumer") -> None:
        user = consumer.scope["user"]
        if consumer.scope["user"].is_authenticated:
            channel = channels.user_channel(user)
            await consumer.unsubscribe(channel)
            consumer.scope["user"] = AnonymousUser()

            await consumer.send_action_response(ActionResponse(action=self))
        else:
            await consumer.send_action_response(
                ActionResponse(action=self, status="error", content={"detail": "not-signed-in"})
            )


class PingAction(PydanticBaseModel):
    command: Literal["ping"] = "ping"

    async def run(self, consumer: "EventConsumer") -> None:
        await consumer.send_action_response(ActionResponse(action=self, content={"message": "pong"}))


# Project


PROJECT_PERMISSIONS = CanViewProject()


async def can_user_subscribe_to_project_channel(user: AbstractUser, project: Project) -> bool:
    try:
        await check_permissions(permissions=PROJECT_PERMISSIONS, user=user, obj=project)
        return True
    except ForbiddenError:
        return False


class SubscribeToProjectEventsAction(PydanticBaseModel):
    command: Literal["subscribe_to_project_events"] = "subscribe_to_project_events"
    project: str

    async def run(self, consumer: "EventConsumer") -> None:
        from projects.projects import services as projects_services

        project_id = decode_b64str_to_uuid(self.project)
        project = await projects_services.get_project(id=project_id)

        if project:
            if await can_user_subscribe_to_project_channel(user=consumer.scope["user"], project=project):
                channel = channels.project_channel(self.project)
                content = {"channel": channel}
                await consumer.subscribe(channel)
                await consumer.send_action_response(ActionResponse(action=self, content=content))
            else:
                # Not enough permissions
                await consumer.send_action_response(
                    ActionResponse(action=self, status="error", content={"detail": "not-allowed"})
                )
        else:
            # Project does not exist
            await consumer.send_action_response(
                ActionResponse(action=self, status="error", content={"detail": "not-found"})
            )


class UnsubscribeFromProjectEventsAction(PydanticBaseModel):
    command: Literal["unsubscribe_from_project_events"] = "unsubscribe_from_project_events"
    project: str

    async def run(self, consumer: "EventConsumer") -> None:
        if consumer.scope["user"].is_authenticated:
            channel = channels.project_channel(self.project)
            ok = await consumer.unsubscribe(channel=channel)
            if ok:
                await consumer.send_action_response(ActionResponse(action=self))
            else:
                await consumer.send_action_response(
                    ActionResponse(action=self, status="error", content={"detail": "not-subscribe"})
                )
        else:
            await consumer.send_action_response(
                ActionResponse(action=self, status="error", content={"detail": "not-allowed"})
            )


class CheckProjectEventsSubscriptionAction(PydanticBaseModel):
    command: Literal["check_project_events_subscription"] = "check_project_events_subscription"
    project: str

    async def run(self, consumer: "EventConsumer") -> None:
        from projects.projects import services as projects_services

        project_id = decode_b64str_to_uuid(self.project)
        project = await projects_services.get_project(id=project_id)

        if project and not await can_user_subscribe_to_project_channel(user=consumer.scope["user"], project=project):
            channel = channels.project_channel(self.project)
            await consumer.unsubscribe(channel=channel)
            await consumer.send_action_response(
                ActionResponse(action=self, status="error", content={"detail": "lost-permissions"})
            )


# workspace

WORKSPACE_PERMISSIONS = HasPerm("view_workspace")


async def can_user_subscribe_to_workspace_channel(user: AbstractUser, workspace: Workspace) -> bool:
    try:
        await check_permissions(permissions=WORKSPACE_PERMISSIONS, user=user, obj=workspace)
        return True
    except ForbiddenError:
        return False


class SubscribeToWorkspaceEventsAction(PydanticBaseModel):
    command: Literal["subscribe_to_workspace_events"] = "subscribe_to_workspace_events"
    workspace: str

    async def run(self, consumer: "EventConsumer") -> None:
        from workspaces.workspaces import services as workspaces_services

        workspace_id = decode_b64str_to_uuid(self.workspace)
        workspace = await workspaces_services.get_workspace(id=workspace_id)

        if workspace:
            if await can_user_subscribe_to_workspace_channel(user=consumer.scope["user"], workspace=workspace):
                channel = channels.workspace_channel(self.workspace)
                content = {"channel": channel}
                await consumer.subscribe(channel=channel)
                await consumer.send_action_response(ActionResponse(action=self, content=content))
            else:
                # Not enough permissions
                await consumer.send_action_response(
                    ActionResponse(action=self, status="error", content={"detail": "not-allowed"})
                )
        else:
            # Workspace does not exist
            await consumer.send_action_response(
                ActionResponse(action=self, status="error", content={"detail": "not-found"})
            )


class UnsubscribeFromWorkspaceEventsAction(PydanticBaseModel):
    command: Literal["unsubscribe_from_workspace_events"] = "unsubscribe_from_workspace_events"
    workspace: str

    async def run(self, consumer: "EventConsumer") -> None:
        if consumer.scope["user"].is_authenticated:
            channel = channels.workspace_channel(self.workspace)
            ok = await consumer.unsubscribe(channel=channel)
            if ok:
                await consumer.send_action_response(ActionResponse(action=self))
            else:
                await consumer.send_action_response(
                    ActionResponse(action=self, status="error", content={"detail": "not-subscribe"})
                )
        else:
            await consumer.send_action_response(
                ActionResponse(action=self, status="error", content={"detail": "not-allowed"})
            )


class CheckWorkspaceEventsSubscriptionAction(PydanticBaseModel):
    command: Literal["check_workspace_events_subscription"] = "check_workspace_events_subscription"
    workspace: str

    async def run(self, consumer: "EventConsumer") -> None:
        from workspaces.workspaces import services as workspaces_services

        workspace_id = decode_b64str_to_uuid(self.workspace)
        workspace = await workspaces_services.get_workspace(id=workspace_id)

        if workspace and not await can_user_subscribe_to_workspace_channel(
            user=consumer.scope["user"], workspace=workspace
        ):
            channel = channels.workspace_channel(self.workspace)
            await consumer.unsubscribe(channel=channel)
            await consumer.send_action_response(
                ActionResponse(action=self, status="error", content={"detail": "lost-permissions"})
            )


ActionList = Annotated[
    Union[
        SignInAction,
        SignOutAction,
        PingAction,
        SubscribeToProjectEventsAction,
        UnsubscribeFromProjectEventsAction,
        CheckProjectEventsSubscriptionAction,
        SubscribeToWorkspaceEventsAction,
        UnsubscribeFromWorkspaceEventsAction,
        CheckWorkspaceEventsSubscriptionAction,
    ],
    Field(..., discriminator="command"),
]


class Action(PydanticBaseModel):
    action: ActionList

    def run(self, consumer: "EventConsumer"):
        raise NotImplementedError


class ActionResponse(PydanticBaseModel):
    type: Literal["action"] = "action"
    action: ActionList
    status: Literal["ok", "error"] = "ok"
    content: dict[str, Any] | None = None


class SystemResponse(PydanticBaseModel):
    type: Literal["system"] = "system"
    status: Literal["ok", "error"] = "ok"
    content: dict[str, Any] | None = None


class EventResponse(PydanticBaseModel):
    type: Literal["event"] = "event"
    channel: str
    event: Event


ResponseList = Annotated[SystemResponse | EventResponse | ActionResponse, Field(..., discriminator="type")]


class Response(PydanticBaseModel):
    response: ResponseList
