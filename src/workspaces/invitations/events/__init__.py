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

from typing import Iterable

from events import events_manager
from workspaces.invitations.events.content import (
    WorkspaceAcceptInvitationContent,
    WorkspaceInvitationContent,
)
from workspaces.invitations.models import WorkspaceInvitation
from workspaces.memberships.models import WorkspaceMembership
from workspaces.workspaces.models import Workspace

CREATE_WORKSPACE_INVITATION = "workspaceinvitations.create"
UPDATE_WORKSPACE_INVITATION = "workspaceinvitations.update"
ACCEPT_WORKSPACE_INVITATION = "workspaceinvitations.accept"
REVOKE_WORKSPACE_INVITATION = "workspaceinvitations.revoke"
DENY_WORKSPACE_INVITATION = "workspaceinvitations.deny"
DELETE_WORKSPACE_INVITATION = "workspaceinvitations.delete"


async def emit_event_when_workspace_invitations_are_created(
    workspace: Workspace,
    invitations: Iterable[WorkspaceInvitation],
) -> None:
    # Publish event on every user channel
    for invitation in filter(lambda i: i.user, invitations):
        await events_manager.publish_on_user_channel(
            user=invitation.user,  # type: ignore[arg-type]
            type=CREATE_WORKSPACE_INVITATION,
            content=WorkspaceInvitationContent(
                workspace_id=invitation.workspace_id, self_recipient=True
            ),
        )

    # Publish on the workspace channel
    if invitations:
        await events_manager.publish_on_workspace_channel(
            workspace=workspace,
            type=CREATE_WORKSPACE_INVITATION,
            content=WorkspaceInvitationContent(
                workspace_id=workspace.id, self_recipient=False
            ),
        )


async def emit_event_when_workspace_invitation_is_updated(
    invitation: WorkspaceInvitation,
) -> None:
    await events_manager.publish_on_workspace_channel(
        workspace=invitation.workspace_id,
        type=UPDATE_WORKSPACE_INVITATION,
        content=WorkspaceInvitationContent(
            workspace_id=invitation.workspace_id, self_recipient=False
        ),
    )
    if invitation.user_id:
        await events_manager.publish_on_user_channel(
            user=invitation.user_id,
            type=UPDATE_WORKSPACE_INVITATION,
            content=WorkspaceInvitationContent(
                workspace_id=invitation.workspace_id, self_recipient=True
            ),
        )


async def emit_event_when_workspace_invitations_are_updated(
    invitations: list[WorkspaceInvitation],
) -> None:
    for invitation in invitations:
        await emit_event_when_workspace_invitation_is_updated(invitation)


async def emit_event_when_workspace_invitation_is_accepted(
    invitation: WorkspaceInvitation, membership: WorkspaceMembership
) -> None:
    content = WorkspaceAcceptInvitationContent(
        workspace_id=invitation.workspace_id,
        membership=membership,
        self_recipient=False,
    )
    await events_manager.publish_on_workspace_channel(
        workspace=invitation.workspace,
        type=ACCEPT_WORKSPACE_INVITATION,
        content=content,
    )
    content.self_recipient = True
    if invitation.user_id:
        await events_manager.publish_on_user_channel(
            user=invitation.user_id,
            type=ACCEPT_WORKSPACE_INVITATION,
            content=content,
        )


async def emit_event_when_workspace_invitation_is_revoked(
    invitation: WorkspaceInvitation,
) -> None:
    await events_manager.publish_on_workspace_channel(
        workspace=invitation.workspace,
        type=REVOKE_WORKSPACE_INVITATION,
        content=WorkspaceInvitationContent(
            workspace_id=invitation.workspace_id, self_recipient=False
        ),
    )
    if invitation.user:
        await events_manager.publish_on_user_channel(
            user=invitation.user,
            type=REVOKE_WORKSPACE_INVITATION,
            content=WorkspaceInvitationContent(
                workspace_id=invitation.workspace_id, self_recipient=True
            ),
        )


async def emit_event_when_workspace_invitation_is_denied(
    invitation: WorkspaceInvitation,
) -> None:
    await events_manager.publish_on_workspace_channel(
        workspace=invitation.workspace,
        type=DENY_WORKSPACE_INVITATION,
        content=WorkspaceInvitationContent(
            workspace_id=invitation.workspace_id, self_recipient=False
        ),
    )
    if invitation.user:
        await events_manager.publish_on_user_channel(
            user=invitation.user,
            type=DENY_WORKSPACE_INVITATION,
            content=WorkspaceInvitationContent(
                workspace_id=invitation.workspace_id, self_recipient=True
            ),
        )


async def emit_event_when_workspace_invitation_is_deleted(
    invitation_or_membership: WorkspaceInvitation | WorkspaceMembership,
) -> None:
    await events_manager.publish_on_workspace_channel(
        workspace=invitation_or_membership.workspace,
        type=DELETE_WORKSPACE_INVITATION,
        content=WorkspaceInvitationContent(
            workspace_id=invitation_or_membership.workspace_id, self_recipient=False
        ),
    )
