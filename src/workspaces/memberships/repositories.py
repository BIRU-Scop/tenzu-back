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

from typing import Literal, TypedDict
from uuid import UUID

from asgiref.sync import sync_to_async
from django.db.models import QuerySet

from users.models import User
from workspaces.memberships.models import WorkspaceMembership
from workspaces.workspaces.models import Workspace

##########################################################
# filters and querysets
##########################################################


DEFAULT_QUERYSET = WorkspaceMembership.objects.all()


class WorkspaceMembershipFilters(TypedDict, total=False):
    id: UUID
    workspace_id: UUID
    user_id: UUID
    username: str


def _apply_filters_to_queryset(
    qs: QuerySet[WorkspaceMembership],
    filters: WorkspaceMembershipFilters = {},
) -> QuerySet[WorkspaceMembership]:
    filter_data = dict(filters.copy())

    if "username" in filters:
        filter_data["user__username"] = filter_data.pop("username")

    return qs.filter(**filter_data)


WorkspaceMembershipSelectRelated = list[
    Literal[
        "user",
        "workspace",
    ]
]


def _apply_select_related_to_queryset(
    qs: QuerySet[WorkspaceMembership],
    select_related: WorkspaceMembershipSelectRelated,
) -> QuerySet[WorkspaceMembership]:
    return qs.select_related(*select_related)


WorkspaceMembershipOrderBy = list[Literal["full_name",]]


def _apply_order_by_to_queryset(
    qs: QuerySet[WorkspaceMembership],
    order_by: WorkspaceMembershipOrderBy,
) -> QuerySet[WorkspaceMembership]:
    order_by_data = []

    for key in order_by:
        if key == "full_name":
            order_by_data.append("user__full_name")
        else:
            order_by_data.append(key)

    return qs.order_by(*order_by_data)


##########################################################
# create workspace membership
##########################################################


@sync_to_async
def create_workspace_membership(
    user: User, workspace: Workspace
) -> WorkspaceMembership:
    return WorkspaceMembership.objects.create(user=user, workspace=workspace)


##########################################################
# list project memberships
##########################################################


@sync_to_async
def list_workspace_memberships(
    filters: WorkspaceMembershipFilters = {},
    select_related: WorkspaceMembershipSelectRelated = [],
    order_by: WorkspaceMembershipOrderBy = ["full_name"],
    offset: int | None = None,
    limit: int | None = None,
) -> list[WorkspaceMembership]:
    qs = _apply_filters_to_queryset(qs=DEFAULT_QUERYSET, filters=filters)
    qs = _apply_select_related_to_queryset(qs=qs, select_related=select_related)
    qs = _apply_order_by_to_queryset(order_by=order_by, qs=qs)

    if limit is not None and offset is not None:
        limit += offset

    return list(qs[offset:limit])


##########################################################
# get workspace membership
##########################################################


@sync_to_async
def get_workspace_membership(
    filters: WorkspaceMembershipFilters = {},
    select_related: WorkspaceMembershipSelectRelated = [],
) -> WorkspaceMembership | None:
    qs = _apply_filters_to_queryset(filters=filters, qs=DEFAULT_QUERYSET)
    qs = _apply_select_related_to_queryset(qs=qs, select_related=select_related)
    try:
        return qs.get()
    except WorkspaceMembership.DoesNotExist:
        return None


##########################################################
# delete workspace memberships
##########################################################


@sync_to_async
def delete_workspace_memberships(filters: WorkspaceMembershipFilters = {}) -> int:
    qs = _apply_filters_to_queryset(qs=DEFAULT_QUERYSET, filters=filters)
    count, _ = qs.delete()
    return count


##########################################################
# misc
##########################################################


@sync_to_async
def list_workspace_members(workspace: Workspace) -> list[User]:
    return list(workspace.members.all())


@sync_to_async
def list_workspace_members_excluding_user(
    workspace: Workspace, exclude_user: User
) -> list[User]:
    return list(workspace.members.all().exclude(id=exclude_user.id))


@sync_to_async
def get_total_workspace_memberships(filters: WorkspaceMembershipFilters = {}) -> int:
    qs = _apply_filters_to_queryset(qs=DEFAULT_QUERYSET, filters=filters)
    return qs.count()
