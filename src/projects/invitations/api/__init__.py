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

from uuid import UUID

from ninja import Path, Router

from commons.exceptions import api as ex
from commons.exceptions.api.errors import (
    ERROR_RESPONSE_400,
    ERROR_RESPONSE_403,
    ERROR_RESPONSE_404,
    ERROR_RESPONSE_422,
)
from commons.validators import B64UUID
from memberships.api.validators import (
    InvitationsValidator,
    UpdateInvitationValidator,
)
from memberships.services.exceptions import (
    BadInvitationTokenError,
    InvitationNonExistingUsernameError,
    OwnerRoleNotAuthorisedError,
)
from permissions import check_permissions
from projects.invitations import services as invitations_services
from projects.invitations.models import ProjectInvitation
from projects.invitations.permissions import ProjectInvitationPermissionsCheck
from projects.invitations.serializers import (
    CreateInvitationsSerializer,
    ProjectInvitationSerializer,
    PublicProjectPendingInvitationSerializer,
)
from projects.projects.api import get_project_or_404

invitations_router = Router()


##########################################################
# create project invitations
##########################################################


@invitations_router.post(
    "/projects/{project_id}/invitations",
    url_name="project.invitations.create",
    summary="Create project invitations",
    response={
        200: CreateInvitationsSerializer,
        400: ERROR_RESPONSE_400,
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def create_project_invitations(
    request,
    project_id: Path[B64UUID],
    form: InvitationsValidator,
) -> CreateInvitationsSerializer:
    """
    Create invitations to a project for a list of users (identified either by their username or their email, and the
    role they'll take in the project). In case of receiving several invitations for the same user, just the first
    role will be considered.
    """
    project = await get_project_or_404(project_id=project_id, get_workspace=True)
    await check_permissions(
        permissions=ProjectInvitationPermissionsCheck.CREATE.value,
        user=request.user,
        obj=project,
    )

    try:
        return await invitations_services.create_project_invitations(
            project=project,
            invitations=form.model_dump()["invitations"],
            invited_by=request.user,
        )
    except InvitationNonExistingUsernameError as e:
        raise ex.BadRequest(str(e))
    except OwnerRoleNotAuthorisedError as e:
        raise ex.ForbiddenError(str(e))


##########################################################
# list project invitations
##########################################################


@invitations_router.get(
    "/projects/{project_id}/invitations",
    url_name="project.invitations.list",
    summary="List project invitations",
    response={
        200: list[ProjectInvitationSerializer],
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def list_project_invitations(
    request,
    project_id: Path[B64UUID],
) -> list[ProjectInvitation]:
    """
    List all project invitations
    """
    project = await get_project_or_404(project_id=project_id)
    await check_permissions(
        permissions=ProjectInvitationPermissionsCheck.VIEW.value,
        user=request.user,
        obj=project,
    )
    return await invitations_services.list_project_invitations(project_id=project_id)


##########################################################
# get project invitation
##########################################################


@invitations_router.get(
    "/projects/invitations/by_token/{token}",
    url_name="project.invitations.get",
    summary="Get public project invitation information by token",
    response={
        200: PublicProjectPendingInvitationSerializer,
        400: ERROR_RESPONSE_400,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
    auth=None,
)
async def get_public_pending_project_invitation(
    request, token: str
) -> PublicProjectPendingInvitationSerializer:
    """
    Get public information about a pending project invitation using a token
    """
    try:
        invitation = await invitations_services.get_public_pending_project_invitation(
            token=token
        )
    except BadInvitationTokenError as e:
        raise ex.BadRequest(str(e))

    except ProjectInvitation.DoesNotExist as e:
        raise ex.NotFoundError("Invitation not found") from e

    return invitation


##########################################################
# resend project invitation
##########################################################


@invitations_router.post(
    "/projects/invitations/{invitation_id}/resend",
    url_name="project.invitations.resend",
    summary="Resend project invitation",
    response={
        200: ProjectInvitationSerializer,
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def resend_project_invitation(
    request,
    invitation_id: Path[B64UUID],
) -> ProjectInvitation:
    """
    Resend invitation to a project
    """
    invitation = await get_project_invitation_or_404(
        invitation_id=invitation_id,
        select_related=["user", "project", "project__workspace"],
    )
    await check_permissions(
        permissions=ProjectInvitationPermissionsCheck.CREATE.value,
        user=request.user,
        obj=invitation.project,
    )
    return await invitations_services.resend_project_invitation(
        invitation=invitation, resent_by=request.user
    )


##########################################################
# revoke project invitation
##########################################################


@invitations_router.post(
    "/projects/invitations/{invitation_id}/revoke",
    url_name="project.invitations.revoke",
    summary="Revoke project invitation",
    response={
        200: ProjectInvitationSerializer,
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def revoke_project_invitation(
    request,
    invitation_id: Path[B64UUID],
) -> ProjectInvitation:
    """
    Revoke invitation in a project.
    """
    invitation = await get_project_invitation_or_404(
        invitation_id=invitation_id, select_related=["user", "project", "role"]
    )
    await check_permissions(
        permissions=ProjectInvitationPermissionsCheck.MODIFY.value,
        user=request.user,
        obj=invitation,
    )
    return await invitations_services.revoke_project_invitation(
        invitation=invitation, revoked_by=request.user
    )


##########################################################
# accept project invitation
##########################################################


@invitations_router.post(
    "/projects/invitations/by_token/{token}/accept",
    url_name="project.invitations.accept",
    summary="Accept project invitation by token",
    response={
        200: ProjectInvitationSerializer,
        400: ERROR_RESPONSE_400,
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def accept_project_invitation_by_token(request, token: str) -> ProjectInvitation:
    """
    A user accepts a project invitation using an invitation token
    """
    try:
        invitation = await get_project_invitation_by_token_or_404(
            token=token, select_related=["user", "project", "role"]
        )
    except BadInvitationTokenError as e:
        raise ex.BadRequest(str(e))
    await check_permissions(
        permissions=ProjectInvitationPermissionsCheck.ANSWER.value,
        user=request.user,
        obj=invitation,
    )
    return await invitations_services.accept_project_invitation(invitation=invitation)


@invitations_router.post(
    "/projects/{project_id}/invitations/accept",
    url_name="project.my.invitations.accept",
    summary="Accept a project invitation for authenticated users",
    response={
        200: ProjectInvitationSerializer,
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def accept_project_invitation_by_project(
    request, project_id: Path[B64UUID]
) -> ProjectInvitation:
    """
    An authenticated user accepts a project invitation
    """
    await check_permissions(
        permissions=ProjectInvitationPermissionsCheck.ANSWER_SELF.value,
        user=request.user,
        obj=None,
    )
    invitation = await get_project_invitation_by_username_or_email_or_404(
        project_id=project_id,
        username_or_email=request.user.username,
        select_related=["user", "project", "role"],
    )
    return await invitations_services.accept_project_invitation(invitation=invitation)


##########################################################
# deny project invitation
##########################################################


@invitations_router.post(
    "/projects/{project_id}/invitations/deny",
    url_name="project.invitations.deny",
    summary="Deny project invitation for authenticated user",
    response={
        200: ProjectInvitationSerializer,
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def deny_project_invitation_by_project(
    request, project_id: Path[B64UUID]
) -> ProjectInvitation:
    """
    An authenticated user denies a project invitation for themself.
    """
    await check_permissions(
        permissions=ProjectInvitationPermissionsCheck.ANSWER_SELF.value,
        user=request.user,
        obj=None,
    )
    invitation = await get_project_invitation_by_username_or_email_or_404(
        project_id=project_id, username_or_email=request.user.username
    )

    return await invitations_services.deny_project_invitation(invitation=invitation)


##########################################################
# update project invitation
##########################################################


@invitations_router.patch(
    "/projects/invitations/{invitation_id}",
    url_name="project.invitations.update",
    summary="Update project invitation",
    response={
        200: ProjectInvitationSerializer,
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def update_project_invitation(
    request,
    invitation_id: Path[B64UUID],
    form: UpdateInvitationValidator,
) -> ProjectInvitation:
    """
    Update project invitation
    """
    invitation = await get_project_invitation_or_404(
        invitation_id=invitation_id, select_related=["user", "project", "role"]
    )
    await check_permissions(
        permissions=ProjectInvitationPermissionsCheck.MODIFY.value,
        user=request.user,
        obj=invitation,
    )

    try:
        return await invitations_services.update_project_invitation(
            invitation=invitation,
            role_id=form.role_id,
            user=request.user,
        )
    except OwnerRoleNotAuthorisedError as e:
        raise ex.ForbiddenError(str(e))


##########################################################
# misc
##########################################################


async def get_project_invitation_by_username_or_email_or_404(
    project_id: UUID,
    username_or_email: str,
    select_related: invitations_services.ProjectInvitationSelectRelated = [
        "user",
        "project",
    ],
) -> ProjectInvitation:
    try:
        invitation = (
            await invitations_services.get_project_invitation_by_username_or_email(
                project_id=project_id,
                username_or_email=username_or_email,
                select_related=select_related,
            )
        )
    except ProjectInvitation.DoesNotExist as e:
        raise ex.NotFoundError("Invitation not found") from e

    return invitation


async def get_project_invitation_or_404(
    invitation_id: UUID,
    select_related: invitations_services.ProjectInvitationSelectRelated = [
        "user",
        "project",
    ],
) -> ProjectInvitation:
    try:
        invitation = await invitations_services.get_project_invitation(
            invitation_id=invitation_id, select_related=select_related
        )
    except ProjectInvitation.DoesNotExist as e:
        raise ex.NotFoundError("Invitation not found") from e

    return invitation


async def get_project_invitation_by_token_or_404(
    token: str,
    select_related: invitations_services.ProjectInvitationSelectRelated = [
        "user",
        "project",
    ],
) -> ProjectInvitation:
    try:
        invitation = await invitations_services.get_project_invitation_by_token(
            token=token, select_related=select_related
        )
    except ProjectInvitation.DoesNotExist as e:
        raise ex.NotFoundError("Invitation does not exist") from e

    return invitation
