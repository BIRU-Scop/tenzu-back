# -*- coding: utf-8 -*-
# Copyright (C) 2024-2025 BIRU
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

from asgiref.sync import sync_to_async
from django.conf import settings

from auth import services as auth_services
from base.api.pagination import Pagination
from commons.colors import generate_random_color
from commons.utils import transaction_atomic_async, transaction_on_commit_async
from emails.emails import Emails
from emails.tasks import send_email
from memberships.choices import InvitationStatus
from memberships.services import exceptions as invitations_ex
from memberships.services.exceptions import MembershipIsTheOnlyOwnerError
from ninja_jwt.exceptions import TokenError
from ninja_jwt.utils import aware_utcnow
from projects.invitations import events as pj_invitations_events
from projects.invitations import repositories as pj_invitations_repositories
from projects.invitations import services as project_invitations_services
from projects.invitations.models import ProjectInvitation
from projects.memberships import events as pj_memberships_events
from projects.memberships import repositories as pj_memberships_repositories
from projects.memberships.models import ProjectMembership
from projects.projects import services as projects_services
from projects.projects.models import Project
from users import events as users_events
from users import repositories as users_repositories
from users.models import User
from users.serializers import UserDeleteInfoSerializer, VerificationInfoSerializer
from users.services import exceptions as ex
from users.tokens import ResetPasswordToken, VerifyUserToken
from workspaces.invitations import events as ws_invitations_events
from workspaces.invitations import repositories as ws_invitations_repositories
from workspaces.invitations import services as workspace_invitations_services
from workspaces.invitations.models import WorkspaceInvitation
from workspaces.memberships import events as ws_memberships_events
from workspaces.memberships import repositories as ws_memberships_repositories
from workspaces.memberships.models import WorkspaceMembership
from workspaces.workspaces import events as workspaces_events
from workspaces.workspaces import repositories as workspaces_repositories
from workspaces.workspaces.models import Workspace

#####################################################################
# create user
#####################################################################


async def create_user(
    email: str,
    full_name: str,
    password: str,
    lang: str | None = None,
    color: int | None = None,
    project_invitation_token: str | None = None,
    accept_project_invitation: bool = True,
    workspace_invitation_token: str | None = None,
    accept_workspace_invitation: bool = True,
) -> User:
    lang = lang if lang else settings.LANGUAGE_CODE
    try:
        user = await users_repositories.get_user(
            q_filter=users_repositories.username_or_email_query(email)
        )
    except User.DoesNotExist:
        # new user
        if not color:
            color = generate_random_color()
        user = await users_repositories.create_user(
            email=email, full_name=full_name, color=color, password=password, lang=lang
        )
    else:
        if user.is_active:
            raise ex.EmailAlreadyExistsError("Email already exists")
        # the user (is_active=False) tries to sign-up again before verifying the previous attempt
        user.full_name = full_name
        user.lang = lang
        user.set_password(password)
        await users_repositories.update_user(user=user)

    await _send_verify_user_email(
        user=user,
        project_invitation_token=project_invitation_token,
        accept_project_invitation=accept_project_invitation,
        workspace_invitation_token=workspace_invitation_token,
        accept_workspace_invitation=accept_workspace_invitation,
    )

    return user


#####################################################################
# verify user
#####################################################################


async def _send_verify_user_email(
    user: User,
    project_invitation_token: str | None = None,
    accept_project_invitation: bool = True,
    workspace_invitation_token: str | None = None,
    accept_workspace_invitation: bool = True,
) -> None:
    context = {
        "verification_token": await _generate_verify_user_token(
            user=user,
            project_invitation_token=project_invitation_token,
            accept_project_invitation=accept_project_invitation,
            workspace_invitation_token=workspace_invitation_token,
            accept_workspace_invitation=accept_workspace_invitation,
        )
    }

    await send_email.defer_async(
        email_name=Emails.SIGN_UP.value,
        to=str(user.email),
        context=context,
        lang=user.lang,
    )


async def _generate_verify_user_token(
    user: User,
    project_invitation_token: str | None = None,
    accept_project_invitation: bool = True,
    workspace_invitation_token: str | None = None,
    accept_workspace_invitation: bool = True,
) -> str:
    verify_user_token = await sync_to_async(VerifyUserToken.for_user)(user)
    if project_invitation_token:
        verify_user_token["project_invitation_token"] = project_invitation_token
        if accept_project_invitation:
            verify_user_token["accept_project_invitation"] = accept_project_invitation

    elif workspace_invitation_token:
        verify_user_token["workspace_invitation_token"] = workspace_invitation_token
        if accept_workspace_invitation:
            verify_user_token["accept_workspace_invitation"] = (
                accept_workspace_invitation
            )

    return str(verify_user_token)


@transaction_atomic_async
async def verify_user(user: User) -> None:
    await users_repositories.update_user(
        user=user, values={"is_active": True, "date_verification": aware_utcnow()}
    )
    await workspace_invitations_services.update_user_workspaces_invitations(user=user)
    await project_invitations_services.update_user_projects_invitations(user=user)


@transaction_atomic_async
async def verify_user_from_token(token: str) -> VerificationInfoSerializer:
    # Get token and deny it
    try:
        verify_token = await sync_to_async(VerifyUserToken)(token)
    except TokenError:
        raise ex.BadVerifyUserTokenError("Invalid or expired token.")

    await sync_to_async(verify_token.blacklist)()

    # Get user and verify it
    try:
        user = await users_repositories.get_user(
            filters={
                settings.NINJA_JWT["USER_ID_FIELD"]: verify_token.get(
                    settings.NINJA_JWT["USER_ID_CLAIM"]
                )
            }
        )
    except User.DoesNotExist as e:
        raise ex.BadVerifyUserTokenError("The user doesn't exist.") from e

    await verify_user(user=user)

    # The user may have a pending invitation to join a project or a workspace
    project_invitation, workspace_invitation = await _accept_invitations_from_token(
        user=user,
        verify_token=verify_token,
    )

    # Generate auth credentials and attach invitation
    auth = await auth_services.create_auth_credentials(user=user)
    return VerificationInfoSerializer(
        auth=auth,
        project_invitation=project_invitation,
        workspace_invitation=workspace_invitation,
    )


#####################################################################
# list users
#####################################################################


async def list_users_emails_as_dict(
    emails: list[str],
) -> dict[str, User]:
    users = await users_repositories.list_users(
        filters={"is_active": True, "email__iin": emails}
    )
    return {u.email: u for u in users}


async def list_users_usernames_as_dict(
    usernames: list[str],
) -> dict[str, User]:
    users = await users_repositories.list_users(
        filters={"is_active": True, "username__iin": usernames}
    )
    return {u.username: u for u in users}


# search users
async def list_paginated_users_by_text(
    text: str,
    offset: int,
    limit: int,
    workspace_id: UUID | None = None,
    project_id: UUID | None = None,
) -> tuple[Pagination, list[User]]:
    """
    List all the users matching the full-text search criteria in their usernames and/or full names. The response will be
    ***alphabetically ordered in blocks***, according to their proximity to a *<project/workspace>* when any of
    these two parameters are received:
      - 1st ordering block: *<project / workspace>* members,
      - 2nd ordering block: *<members of the project's workspace / members of the workspace's projects>*
      - 3rd ordering block: rest of the users
    """
    if workspace_id:
        users = await users_repositories.list_workspace_users_by_text(
            text_search=text, workspace_id=workspace_id, offset=offset, limit=limit
        )
    else:
        users = await users_repositories.list_project_users_by_text(
            text_search=text, project_id=project_id, offset=offset, limit=limit
        )

    pagination = Pagination(offset=offset, limit=limit)

    return pagination, users


#####################################################################
# update user
#####################################################################


async def update_user(user: User, full_name: str, lang: str, password: str) -> User:
    if password:
        user.set_password(password)
    updated_user = await users_repositories.update_user(
        user=user,
        values={"full_name": full_name, "lang": lang},
    )
    return updated_user


#####################################################################
# delete user
#####################################################################


@transaction_atomic_async
async def delete_user(user: User) -> bool:
    # Check that there is no workspace or project where the user is the only owner and there are other members
    if await ws_memberships_repositories.only_owner_queryset(
        Workspace, user, is_collective=True
    ).aexists():
        raise MembershipIsTheOnlyOwnerError(
            "Can't delete a user when they are still the only owner of some workspaces"
        )
    if await pj_memberships_repositories.only_owner_queryset(
        Project, user, is_collective=True
    ).aexists():
        raise MembershipIsTheOnlyOwnerError(
            "Can't delete a user when they are still the only owner of some projects"
        )

    # delete projects where the user is the only pj member
    # (all members, invitations, pj-roles, stories, comments, etc
    # will be deleted in cascade)
    # (We need to delete all projects before workspaces to emit all events)
    async for pj in pj_memberships_repositories.only_project_member_queryset(
        user
    ).select_related("workspace"):
        await projects_services.delete_project(project=pj, deleted_by=user)

    # delete workspaces where the user is the only ws member
    async for ws in ws_memberships_repositories.only_workspace_member_queryset(user):
        # We do not need to delete associated projects: this has been handled by previous
        # projects deletion since when user become project member they also become workspace member
        ws_deleted = await workspaces_repositories.delete_workspace(workspace_id=ws.id)
        if ws_deleted > 0:
            await transaction_on_commit_async(
                workspaces_events.emit_event_when_workspace_is_deleted
            )(workspace=ws, deleted_by=user)

    # send event for related object deletion, actual deletion will be handled by CASCADE
    # event for deletion of ws memberships
    ws_memberships = await ws_memberships_repositories.list_memberships(
        WorkspaceMembership,
        filters={"user_id": user.id},
        select_related=["user", "workspace"],
    )
    for ws_membership in ws_memberships:
        await transaction_on_commit_async(
            ws_memberships_events.emit_event_when_workspace_membership_is_deleted
        )(membership=ws_membership)

    # event for deletion of ws invitations
    ws_invitations = await ws_invitations_repositories.list_invitations(
        WorkspaceInvitation,
        filters={"user": user},
        select_related=["workspace"],
    )
    for ws_invitation in ws_invitations:
        await transaction_on_commit_async(
            ws_invitations_events.emit_event_when_workspace_invitation_is_deleted
        )(invitation_or_membership=ws_invitation)

    # event for deletion of pj memberships
    pj_memberships = await pj_memberships_repositories.list_memberships(
        ProjectMembership,
        filters={"user_id": user.id},
        select_related=["user", "project"],
    )
    for pj_membership in pj_memberships:
        await transaction_on_commit_async(
            pj_memberships_events.emit_event_when_project_membership_is_deleted
        )(membership=pj_membership, workspace_id=pj_membership.project.workspace_id)

    # event for deletion of pj invitations
    pj_invitations = await pj_invitations_repositories.list_invitations(
        ProjectInvitation,
        filters={"user": user},
        select_related=["project"],
    )
    for pj_invitation in pj_invitations:
        await transaction_on_commit_async(
            pj_invitations_events.emit_event_when_project_invitation_is_deleted
        )(
            invitation_or_membership=pj_invitation,
            workspace_id=pj_invitation.project.workspace_id,
        )

    # delete user
    deleted_user = await users_repositories.delete_user(user)

    if deleted_user > 0:
        await transaction_on_commit_async(users_events.emit_event_when_user_is_deleted)(
            user=user
        )
        return True

    return False


async def get_user_delete_info(user: User) -> UserDeleteInfoSerializer:
    only_owner_collective_workspaces = [
        ws
        async for ws in ws_memberships_repositories.only_owner_queryset(
            Workspace, user, is_collective=True
        )
    ]
    only_owner_collective_projects = [
        pj
        async for pj in pj_memberships_repositories.only_owner_queryset(
            Project, user, is_collective=True
        )
    ]
    only_member_workspaces = [
        ws
        async for ws in ws_memberships_repositories.only_workspace_member_queryset(
            user, prefetch_related=[workspaces_repositories.PROJECT_PREFETCH]
        )
    ]
    only_member_projects = [
        pj
        async for pj in pj_memberships_repositories.only_project_member_queryset(
            user, excludes={"workspace__in": only_member_workspaces}
        )
    ]

    return UserDeleteInfoSerializer(
        only_owner_collective_workspaces=only_owner_collective_workspaces,
        only_owner_collective_projects=only_owner_collective_projects,
        only_member_workspaces=only_member_workspaces,
        only_member_projects=only_member_projects,
    )


#####################################################################
# reset password
#####################################################################


async def _get_user_and_reset_password_token(
    token: str,
) -> tuple[ResetPasswordToken, User]:
    try:
        reset_token = await sync_to_async(ResetPasswordToken)(token)
    except TokenError:
        raise ex.BadResetPasswordTokenError("Invalid or expired token.")

    # Get user
    try:
        user = await users_repositories.get_user(
            filters={
                settings.NINJA_JWT["USER_ID_FIELD"]: reset_token.get(
                    settings.NINJA_JWT["USER_ID_CLAIM"]
                ),
                "is_active": True,
            }
        )

    except User.DoesNotExist as e:
        await sync_to_async(reset_token.blacklist)()
        raise ex.BadResetPasswordTokenError("Invalid or malformed token.") from e

    return reset_token, user


async def _generate_reset_password_token(user: User) -> str:
    return str(await sync_to_async(ResetPasswordToken.for_user)(user))


async def _send_reset_password_email(user: User) -> None:
    context = {"reset_password_token": await _generate_reset_password_token(user)}
    await sync_to_async(send_email.defer)(
        email_name=Emails.RESET_PASSWORD.value,
        to=user.email,
        context=context,
        lang=user.lang,
    )


async def request_reset_password(email: str) -> None:
    try:
        user = await users_repositories.get_user(
            filters={"is_active": True},
            q_filter=users_repositories.username_or_email_query(email),
        )
    except User.DoesNotExist:
        pass
    else:
        await _send_reset_password_email(user)


async def verify_reset_password_token(token: str) -> bool:
    return bool(await _get_user_and_reset_password_token(token))


async def reset_password(token: str, password: str) -> User | None:
    reset_token, user = await _get_user_and_reset_password_token(token)

    if user:
        await users_repositories.change_password(user=user, password=password)
        await sync_to_async(reset_token.blacklist)()
        return user

    return None


#####################################################################
# misc
#####################################################################


async def clean_expired_users() -> None:
    await users_repositories.clean_expired_users()


async def _accept_invitations_from_token(
    user: User, verify_token: VerifyUserToken
) -> tuple[ProjectInvitation | None, WorkspaceInvitation | None]:
    workspace_invitation_token = verify_token.get("workspace_invitation_token", None)
    if workspace_invitation_token:
        workspace_invitation = await _accept_workspace_invitation_from_token(
            invitation_token=workspace_invitation_token,
            accept_invitation=verify_token.get("accept_workspace_invitation", False),
            user=user,
        )
        return None, workspace_invitation

    project_invitation_token = verify_token.get("project_invitation_token", None)
    if project_invitation_token:
        project_invitation = await _accept_project_invitation_from_token(
            invitation_token=project_invitation_token,
            accept_invitation=verify_token.get("accept_project_invitation", False),
            user=user,
        )
        return project_invitation, None

    return None, None


async def _accept_project_invitation_from_token(
    invitation_token: str, accept_invitation: bool, user: User
) -> ProjectInvitation | None:
    # Accept project invitation, if it exists and the user comes from the email's CTA. Errors will be ignored
    invitation = None
    if accept_invitation and invitation_token:
        try:
            await project_invitations_services.accept_project_invitation_from_token(
                token=invitation_token,
                user=user,
            )
        except (
            invitations_ex.BadInvitationTokenError,
            invitations_ex.InvitationDoesNotExistError,
            invitations_ex.InvitationIsNotForThisUserError,
            invitations_ex.InvitationAlreadyAcceptedError,
            invitations_ex.InvitationRevokedError,
        ):
            pass  # TODO: Logging invitation is invalid
    if invitation_token:
        try:
            invitation = (
                await project_invitations_services.get_project_invitation_by_token(
                    token=invitation_token
                )
            )
        except (
            invitations_ex.BadInvitationTokenError,
            ProjectInvitation.DoesNotExist,
        ):
            pass  # TODO: Logging invitation is invalid
    return invitation


async def _accept_workspace_invitation_from_token(
    invitation_token: str, accept_invitation: bool, user: User
) -> WorkspaceInvitation | None:
    # Accept workspace invitation, if it exists and the user comes from the email's CTA. Errors will be ignored
    invitation = None
    if accept_invitation and invitation_token:
        try:
            await workspace_invitations_services.accept_workspace_invitation_from_token(
                token=invitation_token,
                user=user,
            )
        except (
            invitations_ex.BadInvitationTokenError,
            invitations_ex.InvitationDoesNotExistError,
            invitations_ex.InvitationIsNotForThisUserError,
            invitations_ex.InvitationAlreadyAcceptedError,
            invitations_ex.InvitationRevokedError,
        ):
            pass  # TODO: Logging invitation is invalid
    if invitation_token:
        try:
            invitation = (
                await workspace_invitations_services.get_workspace_invitation_by_token(
                    token=invitation_token
                )
            )
        except (
            invitations_ex.BadInvitationTokenError,
            WorkspaceInvitation.DoesNotExist,
        ):
            pass  # TODO: Logging invitation is invalid
    return invitation
