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

from base.api.permissions import check_permissions
from base.validators import B64UUID
from exceptions import api as ex
from exceptions.api.errors import ERROR_RESPONSE_400, ERROR_RESPONSE_403, ERROR_RESPONSE_404, ERROR_RESPONSE_422
from ninja_jwt.authentication import AsyncJWTAuth
from permissions import IsAuthenticated, IsProjectAdmin
from projects.invitations import services as invitations_services
from projects.invitations.api.validators import (
    ProjectInvitationsValidator,
    ResendProjectInvitationValidator,
    RevokeProjectInvitationValidator,
    UpdateProjectInvitationValidator,
)
from projects.invitations.models import ProjectInvitation
from projects.invitations.permissions import IsProjectInvitationRecipient
from projects.invitations.serializers import (
    CreateProjectInvitationsSerializer,
    ProjectInvitationSerializer,
    PublicProjectInvitationSerializer,
)
from projects.invitations.services.exceptions import BadInvitationTokenError, NonExistingUsernameError
from projects.projects.api import get_project_or_404

invitations_router = Router(auth=AsyncJWTAuth())

# PERMISSIONS
ACCEPT_PROJECT_INVITATION = IsAuthenticated()
ACCEPT_PROJECT_INVITATION_BY_TOKEN = IsProjectInvitationRecipient()
CREATE_PROJECT_INVITATIONS = IsProjectAdmin()
RESEND_PROJECT_INVITATION = IsProjectAdmin()
REVOKE_PROJECT_INVITATION = IsProjectAdmin()
UPDATE_PROJECT_INVITATION = IsProjectAdmin()


##########################################################
# create project invitations
##########################################################


@invitations_router.post(
    "/projects/{id}/invitations",
    url_name="project.invitations.create",
    summary="Create project invitations",
    response={
        200: CreateProjectInvitationsSerializer,
        400: ERROR_RESPONSE_400,
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
# TODO: remove "Query" from the "id" parameter
async def create_project_invitations(
    request,
    id: Path[B64UUID],
    form: ProjectInvitationsValidator,
) -> CreateProjectInvitationsSerializer:
    """
    Create invitations to a project for a list of users (identified either by their username or their email, and the
    role they'll take in the project). In case of receiving several invitations for the same user, just the first
    role will be considered.
    """
    project = await get_project_or_404(id=id)
    await check_permissions(permissions=CREATE_PROJECT_INVITATIONS, user=request.user, obj=project)

    try:
        return await invitations_services.create_project_invitations(
            project=project,
            invitations=form.model_dump()["invitations"],
            invited_by=request.user,
        )
    except NonExistingUsernameError as e:
        raise ex.BadRequest(str(e))


##########################################################
# list project invitations
##########################################################


@invitations_router.get(
    "/projects/{id}/invitations",
    url_name="project.invitations.list",
    summary="List project pending invitations",
    response={
        200: list[ProjectInvitationSerializer],
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def list_project_invitations(
    request,
    id: Path[B64UUID],
) -> list[ProjectInvitation]:
    """
    List (pending) project invitations
    If the user is a project admin: return the pending project invitation list
    If the user is invited to the project: return a list with just her project invitation
    If the user is not invited to the project (including anonymous users): return an empty list
    """
    project = await get_project_or_404(id)
    return await invitations_services.list_pending_project_invitations(project=project, user=request.user)


##########################################################
# get project invitation
##########################################################


@invitations_router.get(
    "/projects/invitations/{token}",
    url_name="project.invitations.get",
    summary="Get public information about a project invitation",
    response={
        200: PublicProjectInvitationSerializer,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
    auth=None,
)
async def get_public_project_invitation(request, token: str) -> PublicProjectInvitationSerializer:
    """
    Get public information about a project invitation
    """
    try:
        invitation = await invitations_services.get_public_project_invitation(token=token)
    except BadInvitationTokenError:
        raise ex.NotFoundError("Invitation not found")

    if not invitation:
        raise ex.NotFoundError("Invitation not found")

    return invitation


##########################################################
# resend project invitation
##########################################################


@invitations_router.post(
    "/projects/{id}/invitations/resend",
    url_name="project.invitations.resend",
    summary="Resend project invitation",
    response={
        204: None,
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def resend_project_invitation(
    request,
    id: Path[B64UUID],
    form: ResendProjectInvitationValidator,
) -> tuple[int, None]:
    """
    Resend invitation to a project
    """
    invitation = await get_project_invitation_by_username_or_email_or_404(
        project_id=id, username_or_email=form.username_or_email
    )
    await check_permissions(permissions=RESEND_PROJECT_INVITATION, user=request.user, obj=invitation)
    await invitations_services.resend_project_invitation(invitation=invitation, resent_by=request.user)
    return 204, None


##########################################################
# revoke project invitation
##########################################################


@invitations_router.post(
    "/projects/{id}/invitations/revoke",
    url_name="project.invitations.revoke",
    summary="Revoke project invitation",
    response={
        204: None,
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def revoke_project_invitation(
    request,
    id: Path[B64UUID],
    form: RevokeProjectInvitationValidator,
) -> tuple[int, None]:
    """
    Revoke invitation in a project.
    """
    invitation = await get_project_invitation_by_username_or_email_or_404(
        project_id=id, username_or_email=form.username_or_email
    )
    await check_permissions(permissions=REVOKE_PROJECT_INVITATION, user=request.user, obj=invitation)
    await invitations_services.revoke_project_invitation(invitation=invitation, revoked_by=request.user)
    return 204, None


##########################################################
# accept project invitation
##########################################################


@invitations_router.post(
    "/projects/invitations/{token}/accept",
    url_name="project.invitations.accept",
    summary="Accept a project invitation using a token",
    response={
        200: ProjectInvitationSerializer,
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
    invitation = await get_project_invitation_by_token_or_404(token=token)
    await check_permissions(
        permissions=ACCEPT_PROJECT_INVITATION_BY_TOKEN,
        user=request.user,
        obj=invitation,
    )
    return await invitations_services.accept_project_invitation(invitation=invitation)


@invitations_router.post(
    "/projects/{id}/invitations/accept",
    url_name="project.my.invitations.accept",
    summary="Accept a project invitation for authenticated users",
    response={
        200: ProjectInvitationSerializer,
        400: ERROR_RESPONSE_400,
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def accept_project_invitation_by_project(request, id: Path[B64UUID]) -> ProjectInvitation:
    """
    An authenticated user accepts a project invitation
    """
    await check_permissions(permissions=ACCEPT_PROJECT_INVITATION, user=request.user, obj=None)
    invitation = await get_project_invitation_by_username_or_email_or_404(
        project_id=id, username_or_email=request.user.username
    )
    return await invitations_services.accept_project_invitation(invitation=invitation)


##########################################################
# update project invitation
##########################################################


@invitations_router.patch(
    "/projects/{project_id}/invitations/{id}",
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
    id: Path[UUID],
    project_id: Path[B64UUID],
    form: UpdateProjectInvitationValidator,
) -> ProjectInvitation:
    """
    Update project invitation
    """
    invitation = await get_project_invitation_by_id_or_404(project_id=project_id, id=id)
    await check_permissions(permissions=UPDATE_PROJECT_INVITATION, user=request.user, obj=invitation)

    return await invitations_services.update_project_invitation(invitation=invitation, role_slug=form.role_slug)


##########################################################
# misc
##########################################################


async def get_project_invitation_by_username_or_email_or_404(
    project_id: UUID, username_or_email: str
) -> ProjectInvitation:
    try:
        invitation = await invitations_services.get_project_invitation_by_username_or_email(
            project_id=project_id, username_or_email=username_or_email
        )
    except BadInvitationTokenError:
        raise ex.NotFoundError("Invitation not found")
    if not invitation:
        raise ex.NotFoundError("Invitation does not exist")

    return invitation


async def get_project_invitation_by_id_or_404(project_id: UUID, id: UUID) -> ProjectInvitation:
    try:
        invitation = await invitations_services.get_project_invitation_by_id(project_id=project_id, id=id)
    except BadInvitationTokenError:
        raise ex.NotFoundError("Invitation not found")
    if not invitation:
        raise ex.NotFoundError("Invitation does not exist")

    return invitation


async def get_project_invitation_by_token_or_404(token: str) -> ProjectInvitation:
    try:
        invitation = await invitations_services.get_project_invitation(token=token)
    except BadInvitationTokenError:
        raise ex.NotFoundError("Invitation not found")
    if not invitation:
        raise ex.NotFoundError("Invitation does not exist")

    return invitation
