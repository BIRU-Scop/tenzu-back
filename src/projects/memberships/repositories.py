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
from django.db.models import QuerySet

from projects.memberships.models import ProjectMembership
from projects.projects.models import Project
from projects.roles.models import ProjectRole
from users.models import User

##########################################################
# filters and querysets
##########################################################

DEFAULT_QUERYSET = ProjectMembership.objects.all()


class ProjectMembershipFilters(TypedDict, total=False):
    id: UUID
    project_id: UUID
    username: str
    user_id: UUID
    workspace_id: UUID
    role_id: UUID
    permissions: list[str]


def _apply_filters_to_queryset(
    qs: QuerySet[ProjectMembership],
    filters: ProjectMembershipFilters = {},
) -> QuerySet[ProjectMembership]:
    filter_data = dict(filters.copy())

    if "username" in filter_data:
        filter_data["user__username"] = filter_data.pop("username")

    if "workspace_id" in filter_data:
        filter_data["project__workspace_id"] = filter_data.pop("workspace_id")

    if "permissions" in filter_data:
        filter_data["role__permissions__contains"] = filter_data.pop("permissions")

    return qs.filter(**filter_data)


ProjectMembershipSelectRelated = list[
    Literal[
        "project",
        "role",
        "user",
        "workspace",
    ]
]


def _apply_select_related_to_queryset(
    qs: QuerySet[ProjectMembership],
    select_related: ProjectMembershipSelectRelated,
) -> QuerySet[ProjectMembership]:
    select_related_data = []

    for key in select_related:
        if key == "workspace":
            select_related_data.append("project__workspace")
        else:
            select_related_data.append(key)

    return qs.select_related(*select_related_data)


ProjectMembershipOrderBy = list[Literal["full_name",]]


def _apply_order_by_to_queryset(
    qs: QuerySet[ProjectMembership],
    order_by: ProjectMembershipOrderBy,
) -> QuerySet[ProjectMembership]:
    order_by_data = []

    for key in order_by:
        if key == "full_name":
            order_by_data.append("user__full_name")
        else:
            order_by_data.append(key)

    return qs.order_by(*order_by_data)


##########################################################
# create project membership
##########################################################


@sync_to_async
def create_project_membership(
    user: User, project: Project, role: ProjectRole
) -> ProjectMembership:
    return ProjectMembership.objects.create(user=user, project=project, role=role)


##########################################################
# list project memberships
##########################################################


@sync_to_async
def list_project_memberships(
    filters: ProjectMembershipFilters = {},
    select_related: ProjectMembershipSelectRelated = [],
    order_by: ProjectMembershipOrderBy = ["full_name"],
    offset: int | None = None,
    limit: int | None = None,
) -> list[ProjectMembership]:
    qs = _apply_filters_to_queryset(qs=DEFAULT_QUERYSET, filters=filters)
    qs = _apply_select_related_to_queryset(qs=qs, select_related=select_related)
    qs = _apply_order_by_to_queryset(order_by=order_by, qs=qs)

    if limit is not None and offset is not None:
        limit += offset

    return list(qs[offset:limit])


##########################################################
# get project membership
##########################################################


@sync_to_async
def get_project_membership(
    filters: ProjectMembershipFilters = {},
    select_related: ProjectMembershipSelectRelated = ["user", "role"],
) -> ProjectMembership | None:
    qs = _apply_filters_to_queryset(qs=DEFAULT_QUERYSET, filters=filters)
    qs = _apply_select_related_to_queryset(qs=qs, select_related=select_related)

    try:
        return qs.get()
    except ProjectMembership.DoesNotExist:
        return None


##########################################################
# update project membership
##########################################################


@sync_to_async
def update_project_membership(
    membership: ProjectMembership, values: dict[str, Any] = {}
) -> ProjectMembership:
    for attr, value in values.items():
        setattr(membership, attr, value)

    membership.save()
    return membership


##########################################################
# delete project membership
##########################################################


@sync_to_async
def delete_project_membership(filters: ProjectMembershipFilters = {}) -> int:
    qs = _apply_filters_to_queryset(qs=DEFAULT_QUERYSET, filters=filters)
    count, _ = qs.delete()
    return count


##########################################################
# misc
##########################################################


@sync_to_async
def list_project_members(project: Project) -> list[User]:
    return list(project.members.all())


@sync_to_async
def list_project_members_excluding_user(
    project: Project, exclude_user: User
) -> list[User]:
    return list(project.members.all().exclude(id=exclude_user.id))


@sync_to_async
def get_total_project_memberships(filters: ProjectMembershipFilters = {}) -> int:
    qs = _apply_filters_to_queryset(qs=DEFAULT_QUERYSET, filters=filters)
    return qs.count()


@sync_to_async
def exist_project_membership(filters: ProjectMembershipFilters = {}) -> bool:
    qs = _apply_filters_to_queryset(qs=DEFAULT_QUERYSET, filters=filters)
    return qs.exists()
