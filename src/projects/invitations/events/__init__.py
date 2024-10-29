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
from projects.invitations.events.content import ProjectInvitationContent
from projects.invitations.models import ProjectInvitation
from projects.projects.models import Project

CREATE_PROJECT_INVITATION = "projectinvitations.create"
UPDATE_PROJECT_INVITATION = "projectinvitations.update"
ACCEPT_PROJECT_INVITATION = "projectmemberships.create"
REVOKE_PROJECT_INVITATION = "projectinvitations.revoke"
DELETE_PROJECT_INVITATION = "projectinvitations.delete"


async def emit_event_when_project_invitations_are_created(
    project: Project, invitations: Iterable[ProjectInvitation]
) -> None:
    # Publish event on every user channel
    for invitation in filter(lambda i: i.user, invitations):
        await events_manager.publish_on_user_channel(
            user=invitation.user,  # type: ignore[arg-type]
            type=CREATE_PROJECT_INVITATION,
            content=ProjectInvitationContent(
                workspace=invitation.project.workspace_id,
                project=invitation.project_id,
            ),
        )

    # Publish on the project channel
    if invitations:
        await events_manager.publish_on_project_channel(
            project=project,
            type=CREATE_PROJECT_INVITATION,
        )


async def emit_event_when_project_invitation_is_updated(
    invitation: ProjectInvitation,
) -> None:
    await events_manager.publish_on_project_channel(
        project=invitation.project,
        type=UPDATE_PROJECT_INVITATION,
    )
    if invitation.user:
        await events_manager.publish_on_user_channel(
            user=invitation.user,
            type=UPDATE_PROJECT_INVITATION,
            content=ProjectInvitationContent(
                workspace=invitation.project.workspace_id,
                project=invitation.project_id,
            ),
        )


async def emit_event_when_project_invitations_are_updated(
    invitations: list[ProjectInvitation],
) -> None:
    for invitation in invitations:
        await emit_event_when_project_invitation_is_updated(invitation)


async def emit_event_when_project_invitation_is_accepted(
    invitation: ProjectInvitation,
) -> None:
    await events_manager.publish_on_project_channel(
        project=invitation.project,
        type=ACCEPT_PROJECT_INVITATION,
    )
    await events_manager.publish_on_workspace_channel(
        workspace=invitation.project.workspace,
        type=ACCEPT_PROJECT_INVITATION,
    )
    if invitation.user:
        await events_manager.publish_on_user_channel(
            user=invitation.user,
            type=ACCEPT_PROJECT_INVITATION,
            content=ProjectInvitationContent(
                workspace=invitation.project.workspace_id,
                project=invitation.project_id,
            ),
        )


async def emit_event_when_project_invitation_is_revoked(
    invitation: ProjectInvitation,
) -> None:
    await events_manager.publish_on_project_channel(
        project=invitation.project,
        type=REVOKE_PROJECT_INVITATION,
    )
    if invitation.user:
        await events_manager.publish_on_user_channel(
            user=invitation.user,
            type=REVOKE_PROJECT_INVITATION,
            content=ProjectInvitationContent(
                workspace=invitation.project.workspace_id,
                project=invitation.project_id,
            ),
        )


async def emit_event_when_project_invitation_is_deleted(
    invitation: ProjectInvitation,
) -> None:
    await events_manager.publish_on_project_channel(
        project=invitation.project,
        type=DELETE_PROJECT_INVITATION,
    )
