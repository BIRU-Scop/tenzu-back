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
from memberships.repositories import WorkspaceInvitationFilters, exists_invitation
from memberships.services import exceptions as ex
from memberships.services import (  # noqa
    has_pending_invitation,
    is_invitation_for_this_user,
)
from ninja_jwt.exceptions import TokenError
from projects.invitations.models import ProjectInvitation
from users.models import AnyUser, User
from workspaces.invitations import events as invitations_events
from workspaces.invitations import repositories as invitations_repositories
from workspaces.invitations.models import WorkspaceInvitation
from workspaces.invitations.serializers import (
    CreateInvitationsSerializer,
    PublicWorkspacePendingInvitationSerializer,
)
from workspaces.invitations.tokens import WorkspaceInvitationToken
from workspaces.memberships import repositories as memberships_repositories
from workspaces.workspaces.models import Workspace

##########################################################
# create workspace invitations
##########################################################


async def create_workspace_invitations(
    workspace: Workspace,
    invitations: list[dict[str, str]],
    invited_by: User,
) -> CreateInvitationsSerializer:
    user_role = getattr(invited_by, "workspace_role", None)
    invitations_to_send, invitations_to_publish, already_members = cast(
        tuple[list[WorkspaceInvitation], list[WorkspaceInvitation], int],
        await memberships_services.create_invitations(
            reference_object=workspace,
            invitations=invitations,
            invited_by=invited_by,
            user_role=user_role,
        ),
    )
    for invitation in invitations_to_send:
        await send_workspace_invitation_email(invitation=invitation)

    if invitations_to_publish:
        await invitations_events.emit_event_when_workspace_invitations_are_created(
            workspace=workspace, invitations=invitations_to_publish
        )

    return CreateInvitationsSerializer(
        invitations=invitations_to_send, already_members=already_members
    )


##########################################################
# list workspace invitations
##########################################################


async def list_workspace_invitations(
    workspace: Workspace,
) -> list[WorkspaceInvitation]:
    return await invitations_repositories.list_invitations(
        WorkspaceInvitation,
        filters={
            "workspace_id": workspace.id,
        },
        select_related=["user", "workspace", "role"],
        order_by=["user__full_name", "email"],
        order_priorities={"status": InvitationStatus.PENDING},
    )


##########################################################
# get workspace invitation
##########################################################


async def get_workspace_invitation(
    token: str, filters: WorkspaceInvitationFilters = {}
) -> WorkspaceInvitation | None:
    try:
        invitation_token = WorkspaceInvitationToken(token=token)
    except TokenError:
        raise ex.BadInvitationTokenError("Invalid or expired token")

    invitation_data = cast(WorkspaceInvitationFilters, invitation_token.object_id_data)
    return await invitations_repositories.get_invitation(
        WorkspaceInvitation,
        filters={**invitation_data, **filters},
        select_related=["user", "workspace", "role"],
    )


async def get_public_pending_workspace_invitation(
    token: str,
) -> PublicWorkspacePendingInvitationSerializer | None:
    invitation = await get_workspace_invitation(
        token=token, filters={"status": InvitationStatus.PENDING}
    )
    available_logins = (
        await auth_services.get_available_user_logins(user=invitation.user)
        if invitation.user
        else []
    )
    return PublicWorkspacePendingInvitationSerializer(
        email=invitation.email,
        existing_user=invitation.user is not None,
        available_logins=available_logins,
        workspace=invitation.workspace,
    )


async def get_workspace_invitation_by_username_or_email(
    workspace_id: UUID, username_or_email: str
) -> WorkspaceInvitation | None:
    return await invitations_repositories.get_invitation(
        WorkspaceInvitation,
        filters={"workspace_id": workspace_id},
        q_filter=invitations_repositories.invitation_username_or_email_query(
            username_or_email
        ),
        select_related=["user", "workspace", "role"],
    )


async def get_workspace_invitation_by_id(
    workspace_id: UUID, invitation_id: UUID
) -> WorkspaceInvitation | None:
    return await invitations_repositories.get_invitation(
        WorkspaceInvitation,
        filters={"workspace_id": workspace_id, "id": invitation_id},
        select_related=["user", "workspace", "role"],
    )


##########################################################
# update workspace invitations
##########################################################


async def update_user_workspaces_invitations(user: User) -> None:
    await invitations_repositories.update_user_invitations(
        WorkspaceInvitation, user=user
    )
    invitations = await invitations_repositories.list_invitations(
        WorkspaceInvitation,
        filters={"user": user, "status": InvitationStatus.PENDING},
        select_related=["workspace"],
    )
    await transaction_on_commit_async(
        invitations_events.emit_event_when_workspace_invitations_are_updated
    )(invitations=invitations)


async def update_workspace_invitation(
    invitation: WorkspaceInvitation, role_slug: str, user: User
) -> WorkspaceInvitation:
    user_role = user.workspace_role
    updated_invitation = await memberships_services.update_invitation(
        invitation=invitation,
        role_slug=role_slug,
        user_role=user_role,
    )
    await transaction_on_commit_async(
        invitations_events.emit_event_when_workspace_invitation_is_updated
    )(invitation=updated_invitation)

    return updated_invitation


##########################################################
# accept workspace invitation
##########################################################


@transaction_atomic_async
async def accept_workspace_invitation(
    invitation: WorkspaceInvitation,
) -> WorkspaceInvitation:
    invitation = await memberships_services.accept_invitation(
        invitation=invitation,
    )

    await memberships_repositories.create_workspace_membership(
        workspace=invitation.workspace, role=invitation.role, user=invitation.user
    )
    await transaction_on_commit_async(
        invitations_events.emit_event_when_workspace_invitation_is_accepted
    )(invitation=invitation)

    return invitation


async def accept_workspace_invitation_from_token(
    token: str, user: User
) -> WorkspaceInvitation:
    try:
        invitation = await get_workspace_invitation(token=token)

    except WorkspaceInvitation.DoesNotExist as e:
        raise ex.InvitationDoesNotExistError("Invitation does not exist") from e

    if not is_invitation_for_this_user(invitation=invitation, user=user):
        raise ex.InvitationIsNotForThisUserError("Invitation is not for this user")

    return await accept_workspace_invitation(invitation=invitation)


##########################################################
# resend workspace invitation
##########################################################


async def resend_workspace_invitation(
    invitation: WorkspaceInvitation, resent_by: User
) -> WorkspaceInvitation:
    resent_invitation = await memberships_services.resend_invitation(
        invitation=invitation, resent_by=resent_by
    )
    if resent_invitation is not None:
        await send_workspace_invitation_email(
            invitation=resent_invitation, is_resend=True
        )
        return resent_invitation
    return invitation


##########################################################
# deny workspace invitation
##########################################################


async def deny_workspace_invitation(
    invitation: WorkspaceInvitation,
) -> WorkspaceInvitation:
    denied_invitation = await memberships_services.deny_invitation(
        invitation=invitation
    )

    await invitations_events.emit_event_when_workspace_invitation_is_denied(
        invitation=denied_invitation
    )

    return denied_invitation


##########################################################
# revoke workspace invitation
##########################################################


async def revoke_workspace_invitation(
    invitation: WorkspaceInvitation, revoked_by: User
) -> WorkspaceInvitation:
    revoked_invitation = await memberships_services.revoke_invitation(
        invitation=invitation, revoked_by=revoked_by
    )

    await invitations_events.emit_event_when_workspace_invitation_is_revoked(
        invitation=revoked_invitation
    )
    return revoked_invitation


##########################################################
# send workspace invitation
##########################################################


async def send_workspace_invitation_email(
    invitation: WorkspaceInvitation,
    is_resend: bool | None = False,
) -> None:
    workspace = invitation.workspace
    sender = invitation.resent_by if is_resend else invitation.invited_by
    receiver = invitation.user
    email = receiver.email if receiver else invitation.email
    invitation_token = await _generate_workspace_invitation_token(invitation)

    context = {
        "invitation_token": invitation_token,
        "workspace_name": workspace.name,
        "workspace_id": workspace.b64id,
        "workspace_color": workspace.color,
        "sender_name": sender.full_name if sender else None,
        "receiver_name": receiver.full_name if receiver else None,
    }

    await sync_to_async(send_email.defer)(
        email_name=Emails.WORKSPACE_INVITATION.value,
        to=email,
        context=context,
        lang=receiver.lang if receiver else settings.LANGUAGE_CODE,
    )


##########################################################
# misc
##########################################################


async def _generate_workspace_invitation_token(invitation: WorkspaceInvitation) -> str:
    return str(await WorkspaceInvitationToken.create_for_object(invitation))


async def has_pending_inner_projects_invitation(
    user: AnyUser, workspace: Workspace
) -> bool:
    if user.is_anonymous:
        return False

    return await exists_invitation(
        ProjectInvitation,
        filters={
            "project__workspace_id": workspace.id,
        },
        q_filter=invitations_repositories.pending_user_invitation_query(user),
    )
