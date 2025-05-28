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

from typing import cast
from uuid import UUID

from asgiref.sync import sync_to_async
from django.conf import settings

from auth import services as auth_services
from commons.utils import transaction_atomic_async, transaction_on_commit_async
from emails.emails import Emails
from emails.tasks import send_email
from memberships import services as memberships_services
from memberships.choices import InvitationStatus
from memberships.repositories import (
    ProjectInvitationFilters,
    ProjectInvitationSelectRelated,
)
from memberships.services import exceptions as ex
from memberships.services import (  # noqa
    has_pending_invitation,
    is_invitation_for_this_user,
)
from ninja_jwt.exceptions import TokenError
from projects.invitations import events as invitations_events
from projects.invitations import repositories as invitations_repositories
from projects.invitations.models import ProjectInvitation
from projects.invitations.serializers import (
    CreateInvitationsSerializer,
    PublicProjectPendingInvitationSerializer,
)
from projects.invitations.tokens import ProjectInvitationToken
from projects.memberships import repositories as memberships_repositories
from projects.projects.models import Project
from users.models import User
from workspaces.invitations import services as workspaces_invitations_services
from workspaces.invitations.models import WorkspaceInvitation
from workspaces.memberships import services as workspaces_memberships_services
from workspaces.memberships.models import WorkspaceMembership

##########################################################
# create project invitations
##########################################################


async def create_project_invitations(
    project: Project,
    invitations: list[dict[str, str]],
    invited_by: User,
) -> CreateInvitationsSerializer:
    user_role = invited_by.project_role
    invitations_to_send, invitations_to_publish, already_members = cast(
        tuple[list[ProjectInvitation], list[ProjectInvitation], int],
        await memberships_services.create_invitations(
            reference_object=project,
            invitations=invitations,
            invited_by=invited_by,
            user_role=user_role,
        ),
    )
    for invitation in invitations_to_send:
        await send_project_invitation_email(
            invitation=invitation, project=project, sender=invited_by
        )

    if invitations_to_publish:
        await invitations_events.emit_event_when_project_invitations_are_created(
            project=project, invitations=invitations_to_publish
        )

    return CreateInvitationsSerializer(
        invitations=invitations_to_send, already_members=already_members
    )


##########################################################
# list project invitations
##########################################################


async def list_project_invitations(project_id: UUID) -> list[ProjectInvitation]:
    return await invitations_repositories.list_invitations(
        ProjectInvitation,
        filters={
            "project_id": project_id,
        },
        select_related=["project", "user"],
        order_by=["user__full_name", "email"],
        order_priorities={"status": InvitationStatus.PENDING},
    )


##########################################################
# get project invitation
##########################################################


async def get_public_pending_project_invitation(
    token: str,
) -> PublicProjectPendingInvitationSerializer | None:
    invitation = await get_project_invitation_by_token(
        token=token, filters={"status": InvitationStatus.PENDING}
    )
    available_logins = (
        await auth_services.get_available_user_logins(user=invitation.user)
        if invitation.user
        else []
    )
    return PublicProjectPendingInvitationSerializer(
        email=invitation.email,
        existing_user=invitation.user is not None,
        available_logins=available_logins,
        project=invitation.project,
    )


async def get_project_invitation_by_token(
    token: str,
    filters: ProjectInvitationFilters = {},
    select_related: ProjectInvitationSelectRelated = [
        "user",
        "project",
    ],
) -> ProjectInvitation:
    try:
        invitation_token = ProjectInvitationToken(token=token)
    except TokenError:
        raise ex.BadInvitationTokenError("Invalid or expired token")

    invitation_data = cast(ProjectInvitationFilters, invitation_token.object_id_data)
    return await invitations_repositories.get_invitation(
        ProjectInvitation,
        filters={**invitation_data, **filters},
        select_related=select_related,
    )


async def get_project_invitation_by_username_or_email(
    project_id: UUID,
    username_or_email: str,
    select_related: ProjectInvitationSelectRelated = [
        "user",
        "project",
    ],
) -> ProjectInvitation:
    return await invitations_repositories.get_invitation(
        ProjectInvitation,
        filters={"project_id": project_id},
        q_filter=invitations_repositories.invitation_username_or_email_query(
            username_or_email
        ),
        select_related=select_related,
    )


async def get_project_invitation(
    invitation_id: UUID,
    select_related: ProjectInvitationSelectRelated = [
        "user",
        "project",
    ],
) -> ProjectInvitation:
    return await invitations_repositories.get_invitation(
        ProjectInvitation,
        filters={"id": invitation_id},
        select_related=select_related,
    )


##########################################################
# update project invitations
##########################################################


async def update_user_projects_invitations(user: User) -> None:
    await invitations_repositories.update_user_invitations(ProjectInvitation, user=user)
    invitations = await invitations_repositories.list_invitations(
        ProjectInvitation,
        filters={"user": user, "status": InvitationStatus.PENDING},
        select_related=["user", "role", "project"],
    )
    await transaction_on_commit_async(
        invitations_events.emit_event_when_project_invitations_are_updated
    )(invitations=invitations)


async def update_project_invitation(
    invitation: ProjectInvitation, role_id: UUID, user: User
) -> ProjectInvitation:
    user_role = user.project_role
    updated_invitation = await memberships_services.update_invitation(
        invitation=invitation,
        role_id=role_id,
        user_role=user_role,
    )
    await transaction_on_commit_async(
        invitations_events.emit_event_when_project_invitation_is_updated
    )(invitation=updated_invitation)

    return updated_invitation


##########################################################
# accept project invitation
##########################################################


@transaction_atomic_async
async def accept_project_invitation(invitation: ProjectInvitation) -> ProjectInvitation:
    await _sync_related_workspace_membership(invitation)
    invitation = await memberships_services.accept_invitation(
        invitation=invitation,
    )

    await memberships_repositories.create_project_membership(
        project=invitation.project, role=invitation.role, user=invitation.user
    )
    await transaction_on_commit_async(
        invitations_events.emit_event_when_project_invitation_is_accepted
    )(invitation=invitation)

    return invitation


async def accept_project_invitation_from_token(
    token: str, user: User
) -> ProjectInvitation:
    try:
        invitation = await get_project_invitation_by_token(
            token=token, select_related=["user", "project", "role"]
        )

    except ProjectInvitation.DoesNotExist as e:
        raise ex.InvitationDoesNotExistError("Invitation does not exist") from e

    if not is_invitation_for_this_user(invitation=invitation, user=user):
        raise ex.InvitationIsNotForThisUserError("Invitation is not for this user")

    return await accept_project_invitation(invitation=invitation)


##########################################################
# resend project invitation
##########################################################


async def resend_project_invitation(
    invitation: ProjectInvitation, resent_by: User
) -> ProjectInvitation:
    resent_invitation = await memberships_services.resend_invitation(
        invitation=invitation, resent_by=resent_by
    )
    if resent_invitation is not None:
        await send_project_invitation_email(
            invitation=resent_invitation, project=invitation.project, sender=resent_by
        )
        return resent_invitation
    return invitation


##########################################################
# deny project invitation
##########################################################


async def deny_project_invitation(invitation: ProjectInvitation) -> ProjectInvitation:
    denied_invitation = await memberships_services.deny_invitation(
        invitation=invitation
    )

    await invitations_events.emit_event_when_project_invitation_is_denied(
        invitation=denied_invitation
    )

    return denied_invitation


##########################################################
# revoke project invitation
##########################################################


async def revoke_project_invitation(
    invitation: ProjectInvitation, revoked_by: User
) -> ProjectInvitation:
    revoked_invitation = await memberships_services.revoke_invitation(
        invitation=invitation, revoked_by=revoked_by
    )

    await invitations_events.emit_event_when_project_invitation_is_revoked(
        invitation=revoked_invitation
    )
    return revoked_invitation


##########################################################
# send project invitation
##########################################################


async def send_project_invitation_email(
    invitation: ProjectInvitation,
    project: Project,
    sender: User,
) -> None:
    receiver = invitation.user
    email = receiver.email if receiver else invitation.email
    invitation_token = await _generate_project_invitation_token(invitation)
    from projects.projects.services import get_logo_small_thumbnail_url

    context = {
        "invitation_token": invitation_token,
        "project_name": project.name,
        "project_id": project.b64id,
        "project_color": project.color,
        "project_image_url": await get_logo_small_thumbnail_url(project.logo),
        "project_workspace": project.workspace.name,
        "sender_name": sender.full_name if sender else None,
        "receiver_name": receiver.full_name if receiver else None,
    }

    await sync_to_async(send_email.defer)(
        email_name=Emails.PROJECT_INVITATION.value,
        to=email,
        context=context,
        lang=receiver.lang if receiver else settings.LANGUAGE_CODE,
    )


##########################################################
# misc
##########################################################


async def _generate_project_invitation_token(invitation: ProjectInvitation) -> str:
    return str(await ProjectInvitationToken.create_for_object(invitation))


async def _sync_related_workspace_membership(pj_invitation: ProjectInvitation):
    # find existing membership first, do nothing then
    if await memberships_repositories.exists_membership(
        WorkspaceMembership,
        filters={
            "workspace_id": pj_invitation.project.workspace_id,
            "user_id": pj_invitation.user_id,
        },
    ):
        return
    # find existing invitation, accept it
    try:
        ws_invitation: WorkspaceInvitation = (
            await invitations_repositories.get_invitation(
                WorkspaceInvitation,
                filters={
                    "workspace_id": pj_invitation.project.workspace_id,
                    "user_id": pj_invitation.user_id,
                    "status": InvitationStatus.PENDING,
                },
                select_related=["user", "workspace", "role"],
            )
        )
    except WorkspaceInvitation.DoesNotExist:
        # there is no existing membership nor pending invitation, create workspace default membership
        await workspaces_memberships_services.create_default_workspace_membership(
            pj_invitation.project.workspace_id, pj_invitation.user
        )
    else:
        await workspaces_invitations_services.accept_workspace_invitation(ws_invitation)
