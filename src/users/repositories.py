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

from typing import Any, Literal, TypedDict
from uuid import UUID

from asgiref.sync import sync_to_async
from django.contrib.auth.models import update_last_login as django_update_last_login
from django.contrib.postgres.lookups import Unaccent
from django.contrib.postgres.search import (
    SearchQuery,
    SearchRank,
    SearchVector,
)
from django.db.models import (
    BooleanField,
    Exists,
    OuterRef,
    Q,
    QuerySet,
    Value,
)
from django.db.models.functions import (
    Lower,
    StrIndex,
)

from memberships.choices import InvitationStatus
from ninja_jwt.token_blacklist.models import OutstandingToken
from projects.invitations.models import ProjectInvitation
from projects.memberships.models import ProjectMembership
from users.models import AuthData, User
from workspaces.invitations.models import WorkspaceInvitation
from workspaces.memberships.models import WorkspaceMembership

##########################################################
# USER - filters and querysets
##########################################################


class UserFilters(TypedDict, total=False):
    id: UUID
    email: str
    email__iin: list[str]
    username__iin: list[str]
    is_active: bool


UserOrderBy = list[
    Literal[
        "full_name",
        "username",
    ]
]


##########################################################
# create user
##########################################################


async def create_user(
    email: str, full_name: str, color: int, lang: str, password: str | None
) -> User:
    user = User(
        email=email,
        full_name=full_name,
        is_active=False,
        accepted_terms=True,
        lang=lang,
        color=color,
    )
    if password:
        user.set_password(password)

    await user.asave()
    return user


##########################################################
# list users
##########################################################


async def list_users(
    filters: UserFilters = {},
    order_by: UserOrderBy = ["full_name"],
    offset: int | None = None,
    limit: int | None = None,
) -> list[User]:
    qs = User.objects.all().filter(**filters)
    qs = qs.order_by(*order_by)

    if limit is not None and offset is not None:
        limit += offset

    return [u async for u in qs[offset:limit]]


##########################################################
# list users - search
##########################################################


async def list_project_users_by_text(
    text_search: str = "",
    project_id: UUID | None = None,
    exclude_inactive: bool = True,
    offset: int | None = None,
    limit: int | None = None,
) -> list[User]:
    qs = _list_project_users_by_text_qs(
        text_search=text_search,
        project_id=project_id,
        exclude_inactive=exclude_inactive,
    )
    if limit is not None and offset is not None:
        limit += offset

    return [u async for u in qs[offset:limit]]


async def list_workspace_users_by_text(
    text_search: str = "",
    workspace_id: UUID | None = None,
    exclude_inactive: bool = True,
    offset: int | None = None,
    limit: int | None = None,
) -> list[User]:
    qs = _list_workspace_users_by_text_qs(
        text_search=text_search,
        workspace_id=workspace_id,
        exclude_inactive=exclude_inactive,
    )
    if limit is not None and offset is not None:
        limit += offset

    return [u async for u in qs[offset:limit]]


def _list_users_by_text_qs(
    text_search: str = "", exclude_inactive: bool = True
) -> QuerySet[User]:
    """
    Get all the users that match a full text search (against their full_name and username fields).

    :param text_search: The text the users should match in either their full names or usernames to be considered
    :param exclude_inactive: true (return just active users), false (returns all users)
    :return: a users queryset
    """
    users_qs = User.objects.all()

    if exclude_inactive:
        users_qs &= users_qs.exclude(is_active=False)

    if text_search:
        users_matching_full_text_search = _list_users_by_fullname_or_username(
            text_search, users_qs
        )
        users_qs = users_matching_full_text_search

    return users_qs


def _list_project_users_by_text_qs(
    text_search: str = "", project_id: UUID | None = None, exclude_inactive: bool = True
) -> QuerySet[User]:
    """
    Get all the users that match a full text search (against their full_name and username fields), returning a
    prioritized (not filtered) list by their closeness to a given project (if any).

    :param text_search: The text the users should match in either their full names or usernames to be considered
    :param project_id: Users will be ordered by their proximity to this project excluding itself
    :param exclude_inactive: true (return just active users), false (returns all users)
    :return: a prioritized queryset of users
    """
    users_qs = _list_users_by_text_qs(
        text_search=text_search, exclude_inactive=exclude_inactive
    )

    if project_id:
        # List all the users matching the full-text search criteria, ordering results by their proximity to a project :
        #     1st. project members of this project
        #     2nd. members of the project's workspace
        #     3rd. rest of users (the priority for this group is not too important)

        # 1st: Users that share the same project
        memberships = ProjectMembership.objects.filter(
            user__id=OuterRef("pk"), project__id=project_id
        )
        pending_invitations = ProjectInvitation.objects.filter(
            user__id=OuterRef("pk"),
            project__id=project_id,
            status=InvitationStatus.PENDING,
        )
        project_users_qs = (
            users_qs.filter(projects__id=project_id)
            .annotate(user_is_member=Exists(memberships))
            .annotate(user_has_pending_invitation=Exists(pending_invitations))
        )
        sorted_project_users_qs = _sort_queryset_if_unsorted(
            project_users_qs, text_search
        )

        # 2nd: Users that are members of the project's workspace but are NOT project members
        workspace_users_qs = (
            users_qs.filter(workspaces__projects__id=project_id)
            .annotate(user_is_member=Value(False, output_field=BooleanField()))
            .annotate(user_has_pending_invitation=Exists(pending_invitations))
            .exclude(projects__id=project_id)
        )
        sorted_workspace_users_qs = _sort_queryset_if_unsorted(
            workspace_users_qs, text_search
        )

        # 3rd: Users that are neither a project member nor a member of its workspace
        other_users_qs = (
            users_qs.exclude(projects__id=project_id)
            .exclude(workspaces__projects__id=project_id)
            .annotate(user_is_member=Value(False, output_field=BooleanField()))
            .annotate(user_has_pending_invitation=Exists(pending_invitations))
        )
        sorted_other_users_qs = _sort_queryset_if_unsorted(other_users_qs, text_search)

        # NOTE: `Union all` are important to keep the individual ordering when combining the different search criteria.
        users_qs = sorted_project_users_qs.union(
            sorted_workspace_users_qs.union(sorted_other_users_qs, all=True), all=True
        )
        return users_qs

    return _sort_queryset_if_unsorted(users_qs, text_search)


def _list_workspace_users_by_text_qs(
    text_search: str = "",
    workspace_id: UUID | None = None,
    exclude_inactive: bool = True,
) -> QuerySet[User]:
    """
    Get all the users that match a full text search (against their full_name and username fields), returning a
    prioritized (not filtered) list by their closeness to a given workspace (if any).

    :param text_search: The text the users should match in either their full names or usernames to be considered
    :param workspace_id: Users will be ordered by their proximity to this workspace excluding itself
    :param exclude_inactive: true (return just active users), false (returns all users)
    :return: a prioritized queryset of users
    """
    users_qs = _list_users_by_text_qs(
        text_search=text_search, exclude_inactive=exclude_inactive
    )

    if workspace_id:
        # List all the users matching the full-text search criteria, ordering results by their proximity to a workspace:
        #     1st. workspace members
        #     2nd. members of the workspace's projects
        #     3rd. rest of users (the priority for this group is not too important)

        # 1st: Users that share the same workspace
        memberships = WorkspaceMembership.objects.filter(
            user__id=OuterRef("pk"), workspace__id=workspace_id
        )
        pending_invitations = WorkspaceInvitation.objects.filter(
            user__id=OuterRef("pk"),
            workspace__id=workspace_id,
            status=InvitationStatus.PENDING,
        )
        workspace_users_qs = (
            users_qs.filter(workspaces__id=workspace_id)
            .annotate(user_is_member=Exists(memberships))
            .annotate(user_has_pending_invitation=Exists(pending_invitations))
        )
        sorted_workspace_users_qs = _sort_queryset_if_unsorted(
            workspace_users_qs, text_search
        )

        # # 2nd: Users that are members of the workspace's projects but are NOT workspace members
        ws_projects_users_qs = (
            users_qs.filter(projects__workspace_id=workspace_id)
            .exclude(workspaces__id=workspace_id)
            .annotate(user_is_member=Value(False, output_field=BooleanField()))
            .annotate(user_has_pending_invitation=Exists(pending_invitations))
            .distinct()
        )
        sorted_ws_projects_users_qs = _sort_queryset_if_unsorted(
            ws_projects_users_qs, text_search
        )

        # 3rd: Users that are neither a workspace member nor a member of the workspace's projects
        other_users_qs = (
            users_qs.exclude(workspaces__id=workspace_id)
            .exclude(projects__workspace_id=workspace_id)
            .annotate(user_is_member=Value(False, output_field=BooleanField()))
            .annotate(user_has_pending_invitation=Exists(pending_invitations))
        )
        sorted_other_users_qs = _sort_queryset_if_unsorted(other_users_qs, text_search)

        # NOTE: `Union all` are important to keep the individual ordering when combining the different search criteria.
        users_qs = sorted_workspace_users_qs.union(
            sorted_ws_projects_users_qs.union(sorted_other_users_qs, all=True), all=True
        )
        return users_qs

    return _sort_queryset_if_unsorted(users_qs, text_search)


def _sort_queryset_if_unsorted(
    users_qs: QuerySet[User], text_search: str
) -> QuerySet[User]:
    if not text_search:
        return users_qs.order_by("full_name", "username")

    # the queryset has already been sorted by the "Full Text Search" and its annotated 'rank' field
    return users_qs


def _list_users_by_fullname_or_username(
    text_search: str, user_qs: QuerySet[User]
) -> QuerySet[User]:
    """
    This method searches for users matching a text in their full names and usernames (being accent and case
    insensitive) and order the results according to:
        1st. Order by full text search rank according to the specified matrix weights (0.5 to both full_name/username)
        2nd. Order by literal matches in full names detected closer to the left, or close to start with that text
        3rd. Order by full name alphabetically
        4th. Order by username alphabetically
    :param text_search: The text to search for (in user full names and usernames)
    :param user_qs: The base user queryset to which apply the filters to
    :return: A filtered queryset that will return an ordered list of users matching the text when executed
    """
    # Prepares the SearchQuery text by escaping it and fixing spaces for searches over several words
    parsed_text_search = repr(text_search.strip()).replace(" ", " & ")
    search_query = SearchQuery(
        f"{parsed_text_search}:*", search_type="raw", config="simple_unaccent"
    )
    search_vector = SearchVector(
        "full_name", weight="A", config="simple_unaccent"
    ) + SearchVector("username", weight="B", config="simple_unaccent")
    # By default values: [0.1, 0.2, 0.4, 1.0]
    # [D-weight, C-weight, B-weight, A-weight]
    rank_weights = [0.0, 0.0, 0.5, 0.5]

    full_text_matching_users = (
        user_qs.annotate(
            rank=SearchRank(search_vector, search_query, weights=rank_weights)
        )
        .annotate(
            first_match=StrIndex(
                Unaccent(Lower("full_name")), Unaccent(Lower(Value(text_search)))
            )
        )
        .filter(rank__gte=0.2)
        .order_by("-rank", "first_match", "full_name", "username")
    )

    return full_text_matching_users


##########################################################
# get user
##########################################################


async def get_user(
    filters: UserFilters = {},
    q_filter: Q | None = None,
) -> User | None:
    qs = User.objects.all().filter(**filters)
    if q_filter:
        qs = qs.filter(q_filter)
    return await qs.aget()


##########################################################
# update user
##########################################################


async def update_user(user: User, values: dict[str, Any] = {}) -> User:
    for attr, value in values.items():
        if value:
            setattr(user, attr, value)

    await user.asave()
    return user


##########################################################
# delete user
##########################################################


async def delete_user(user: User) -> int:
    # don't call user.adelete directly since it will set id to None and we might need it for events
    count, _ = await User.objects.filter(id=user.id).adelete()
    return count


##########################################################
# queries invitation
##########################################################


def username_or_email_query(username_or_email: str) -> Q:
    return Q(username__iexact=username_or_email) | Q(email__iexact=username_or_email)


##########################################################
# misc user
##########################################################


async def check_password(user: User, password: str) -> bool:
    return user.password != "" and await user.acheck_password(password)


async def change_password(user: User, password: str) -> None:
    user.set_password(password)
    await user.asave()


@sync_to_async
def update_last_login(user: User) -> None:
    django_update_last_login(User, user)


async def clean_expired_users() -> None:
    # delete all users that are not currently active (is_active=False)
    # and have never verified the account (date_verification=None)
    # and don't have an outstanding token associated (exclude)
    await (
        User.objects.filter(is_active=False, date_verification=None)
        .exclude(id__in=OutstandingToken.objects.values_list("user_id"))
        .adelete()
    )


async def get_total_workspace_users_by_text(
    text_search: str = "",
    workspace_id: UUID | None = None,
    exclude_inactive: bool = True,
) -> int:
    qs = _list_workspace_users_by_text_qs(
        text_search=text_search,
        workspace_id=workspace_id,
        exclude_inactive=exclude_inactive,
    )
    return await qs.acount()


##########################################################
# AUTH DATA - filters and querysets
##########################################################


DEFAULT_AUTH_DATA_QUERYSET = AuthData.objects.all()


class AuthDataFilters(TypedDict, total=False):
    key: str
    value: str


def _apply_filters_to_auth_data_queryset(
    qs: QuerySet[AuthData],
    filters: AuthDataFilters = {},
) -> QuerySet[AuthData]:
    return qs.filter(**filters)


class AuthDataListFilters(TypedDict, total=False):
    user_id: UUID


def _apply_filters_to_auth_data_queryset_list(
    qs: QuerySet[AuthData],
    filters: AuthDataListFilters = {},
) -> QuerySet[AuthData]:
    return qs.filter(**filters)


AuthDataSelectRelated = list[Literal["user"]]


def _apply_select_related_to_auth_data_queryset(
    qs: QuerySet[AuthData],
    select_related: AuthDataSelectRelated,
) -> QuerySet[AuthData]:
    return qs.select_related(*select_related)


##########################################################
# create auth data
##########################################################


@sync_to_async
def create_auth_data(
    user: User, key: str, value: str, extra: dict[str, str] = {}
) -> AuthData:
    return AuthData.objects.create(user=user, key=key, value=value, extra=extra)


##########################################################
# list auths data
##########################################################


@sync_to_async
def list_auths_data(
    filters: AuthDataListFilters = {},
    select_related: AuthDataSelectRelated = ["user"],
) -> list[AuthData]:
    qs = _apply_filters_to_auth_data_queryset_list(
        qs=DEFAULT_AUTH_DATA_QUERYSET, filters=filters
    )
    qs = _apply_select_related_to_auth_data_queryset(
        qs=qs, select_related=select_related
    )

    return list(qs)


##########################################################
# get auth data
##########################################################


@sync_to_async
def get_auth_data(
    filters: AuthDataFilters = {},
    select_related: AuthDataSelectRelated = ["user"],
) -> AuthData | None:
    qs = _apply_filters_to_auth_data_queryset(
        qs=DEFAULT_AUTH_DATA_QUERYSET, filters=filters
    )
    qs = _apply_select_related_to_auth_data_queryset(
        qs=qs, select_related=select_related
    )

    try:
        return qs.get()
    except AuthData.DoesNotExist:
        return None
