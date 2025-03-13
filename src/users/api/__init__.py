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

from asgiref.sync import sync_to_async
from django.http import HttpResponse
from ninja import Query, Router

from base.api import pagination as api_pagination
from base.api.pagination import PaginationQuery
from base.validators import B64UUID
from commons.exceptions import api as ex
from commons.exceptions.api.errors import (
    ERROR_RESPONSE_400,
    ERROR_RESPONSE_401,
    ERROR_RESPONSE_403,
    ERROR_RESPONSE_422,
)
from ninja_jwt.schema import TokenObtainPairOutputSchema
from ninja_jwt.tokens import RefreshToken
from permissions import IsAuthenticated, check_permissions
from users import services as users_services
from users.api.validators import (
    CreateUserValidator,
    RequestResetPasswordValidator,
    ResetPasswordValidator,
    UpdateUserValidator,
    VerifyTokenValidator,
)
from users.models import User
from users.serializers import (
    UserDeleteInfoSerializer,
    UserSearchSerializer,
    UserSerializer,
    VerificationInfoSerializer,
)

users_router = Router()


#####################################################################
# create user
#####################################################################


@users_router.post(
    "/users",
    url_name="users.create",
    summary="Sign up user",
    by_alias=True,
    auth=None,
    response={200: UserSerializer, 400: ERROR_RESPONSE_400, 422: ERROR_RESPONSE_422},
)
async def create_user(request, form: CreateUserValidator) -> User:
    """
    Create new user, which is not yet verified.
    """
    return await users_services.create_user(
        email=form.email,
        full_name=form.full_name,
        color=form.color,
        password=form.password,
        lang=form.lang,
        project_invitation_token=form.project_invitation_token,
        accept_project_invitation=form.accept_project_invitation,
        workspace_invitation_token=form.workspace_invitation_token,
        accept_workspace_invitation=form.accept_workspace_invitation,
    )


#####################################################################
# create user verify
#####################################################################


@users_router.post(
    "/users/verify",
    url_name="users.verify",
    summary="Verify the account of a new signup user",
    response={
        200: VerificationInfoSerializer,
        400: ERROR_RESPONSE_400,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
    auth=None,
)
async def verify_user(
    request, form: VerifyTokenValidator
) -> VerificationInfoSerializer:
    """
    Verify the account of a new signup user.
    """
    return await users_services.verify_user_from_token(token=form.token)


#####################################################################
# list users (search)
#####################################################################


@users_router.get(
    "/users/search",
    url_name="users.search",
    summary="List all users matching a full text search, ordered (when provided) by their closeness"
    " to a project or a workspace.",
    response={
        200: list[UserSearchSerializer],
        403: ERROR_RESPONSE_403,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
# TODO @paginate
async def list_users_by_text(
    request,
    response: HttpResponse,
    pagination_params: Query[PaginationQuery],
    text: str = None,
    project: Query[B64UUID] = None,
    workspace: Query[B64UUID] = None,
) -> list[User]:
    """
    List all the users matching the full-text search criteria in their usernames and/or full names. The response will be
    ***alphabetically ordered in blocks***, according to their proximity to a *<project/workspace>* when any of
    these two parameters are received:
      - 1st ordering block: *<project / workspace>* members,
      - 2nd ordering block: *<members of the project's workspace / members of the workspace's projects>*
      - 3rd ordering block: rest of the users
    """
    await check_permissions(permissions=IsAuthenticated(), user=request.user)

    pagination, users = await users_services.list_paginated_users_by_text(
        text=text,
        project_id=project,
        workspace_id=workspace,
        offset=pagination_params.offset,
        limit=pagination_params.limit,
    )

    api_pagination.set_pagination(response=response, pagination=pagination)

    return users


#####################################################################
# get user
#####################################################################


@users_router.get(
    "/my/user",
    url_name="my.user",
    summary="Get authenticated user",
    response=UserSerializer,
    by_alias=True,
)
async def get_my_user(request) -> User:
    """
    Get the current authenticated user (according to the auth token in the request headers).
    """

    if request.user.is_anonymous:
        # NOTE: We force a 401 instead of using the permissions system (which would return a 403)
        raise ex.AuthorizationError("User is anonymous")

    return request.user


#####################################################################
# update user
#####################################################################


@users_router.put(
    "/my/user",
    url_name="my.user.update",
    summary="Update authenticated user",
    response={
        200: UserSerializer,
        400: ERROR_RESPONSE_400,
        401: ERROR_RESPONSE_401,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def update_my_user(request, form: UpdateUserValidator) -> User:
    """
    Update the current authenticated user (according to the auth token in the request headers).
    """
    if request.user.is_anonymous:
        # NOTE: We force a 401 instead of using the permissions system (which would return a 403)
        raise ex.AuthorizationError("User is anonymous")

    return await users_services.update_user(
        user=request.user,
        full_name=form.full_name,
        lang=form.lang,
        password=form.password,
    )


#####################################################################
# delete user
#####################################################################


@users_router.delete(
    "/my/user",
    url_name="my.user.delete",
    summary="Delete user",
    response={204: None, 401: ERROR_RESPONSE_401},
    by_alias=True,
)
async def delete_user(request) -> tuple[int, None]:
    """
    Delete a user.

    In this endpoint:
    - All workspaces where the user is the only workspace member are deleted (cascade)
    - All projects where the user is the only project member are deleted (cascade)
    - All projects where the user is the only project admin and is not the only workspace member
    or is not workspace member are updated with a new project admin (a workspace member)
    - All memberships related with this user in workspaces and projects are deleted
    - All invitations related with this user in workspaces and projects are deleted
    - User is deleted
    """
    if request.user.is_anonymous:
        # NOTE: We force a 401 instead of using the permissions system (which would return a 403)
        raise ex.AuthorizationError("User is anonymous")

    await users_services.delete_user(user=request.user)
    return 204, None


#####################################################################
# delete info user
#####################################################################


@users_router.get(
    "/my/user/delete-info",
    url_name="my.user.delete-info",
    summary="Get user delete info",
    response={200: UserDeleteInfoSerializer, 401: ERROR_RESPONSE_401},
    by_alias=True,
)
async def get_user_delete_info(request) -> UserDeleteInfoSerializer:
    """
    Get some info before deleting a user.

    This endpoint returns:
    - A list of workspaces where the user is the only workspace member and the workspace has projects
    - A list projects where the user is the only project admin and is not the only workspace member
    or is not workspace member
    """
    if request.user.is_anonymous:
        # NOTE: We force a 401 instead of using the permissions system (which would return a 403)
        raise ex.AuthorizationError("User is anonymous")

    return await users_services.get_user_delete_info(user=request.user)


#####################################################################
# reset user password
#####################################################################


@users_router.post(
    "/users/reset-password",
    url_name="users.reset-password-request",
    summary="Request a user password reset",
    response={200: bool, 422: ERROR_RESPONSE_422},
    by_alias=True,
    auth=None,
)
async def request_reset_password(request, form: RequestResetPasswordValidator) -> bool:
    """
    Request a user password reset.
    """
    await users_services.request_reset_password(email=form.email)
    return True


#####################################################################
# reset user password verify
#####################################################################


@users_router.get(
    "/users/reset-password/{token}/verify",
    url_name="users.reset-password-verify",
    summary="Verify reset password token",
    response={200: bool, 400: ERROR_RESPONSE_400, 422: ERROR_RESPONSE_422},
    by_alias=True,
    auth=None,
)
async def verify_reset_password_token(request, token: str) -> bool:
    """
    Verify reset password token
    """
    return await users_services.verify_reset_password_token(token=token)


@users_router.post(
    "/users/reset-password/{token}",
    url_name="users.reset-password-change",
    summary="Reset user password",
    response={
        200: TokenObtainPairOutputSchema,
        400: ERROR_RESPONSE_400,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
    auth=None,
)
async def reset_password(
    request,
    token: str,
    form: ResetPasswordValidator,
) -> TokenObtainPairOutputSchema:
    """
    Reset user password
    """
    user = await users_services.reset_password(token=token, password=form.password)

    if not user:
        raise ex.BadRequest(
            "The user is inactive or does not exist.", detail="inactive-user"
        )
    refresh: RefreshToken = await sync_to_async(RefreshToken.for_user)(user)
    username_field = User.USERNAME_FIELD

    return TokenObtainPairOutputSchema(
        access=str(refresh.access_token),
        refresh=str(refresh),
        **{username_field: getattr(user, username_field)},
    )
