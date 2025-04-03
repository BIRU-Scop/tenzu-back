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

from typing import Any, Literal, TypedDict, TypeVar
from uuid import UUID

from memberships.models import Membership, Role


class MembershipFilters(TypedDict, total=False):
    project_id: UUID
    user__username: str
    user_id: UUID
    role__permissions__contains: list[str]


MembershipSelectRelated = list[
    Literal[
        "project",
        "role",
        "user",
    ]
]

MembershipOrderBy = list[Literal["user__full_name",]]
TM = TypeVar("TM", bound=Membership)


class ProjectRoleFilters(TypedDict, total=False):
    project_id: UUID
    slug: str
    memberships__user_id: UUID


ProjectRoleSelectRelated = list[Literal["project",]]
TR = TypeVar("TR", bound=Role)

##########################################################
# list memberships
##########################################################


async def list_memberships(
    model: type[TM],
    filters: MembershipFilters = {},
    select_related: MembershipSelectRelated = [],
    order_by: MembershipOrderBy = ["user__full_name"],
    offset: int | None = None,
    limit: int | None = None,
) -> list[TM]:
    qs = (
        model.objects.all()
        .filter(**filters)
        .select_related(*select_related)
        .order_by(*order_by)
    )

    if limit is not None and offset is not None:
        limit += offset

    return [a async for a in qs[offset:limit]]


##########################################################
# get membership
##########################################################


async def get_membership(
    model: type[TM],
    filters: MembershipFilters = {},
    select_related: MembershipSelectRelated = ["user", "role"],
) -> TM:
    qs = model.objects.all().filter(**filters).select_related(*select_related)
    return await qs.aget()


##########################################################
# update membership
##########################################################


async def update_membership(membership: TM, values: dict[str, Any] = {}) -> TM:
    for attr, value in values.items():
        setattr(membership, attr, value)

    await membership.asave()
    return membership


##########################################################
# delete membership
##########################################################


async def delete_membership(membership: TM) -> int:
    count, _ = await membership.adelete()
    return count


##########################################################
# misc membership
##########################################################


async def has_other_owner_memberships(model: type[TM], exclude_id: UUID):
    return (
        await model.objects.all()
        .filter(role__is_owner=True)
        .exclude(id=exclude_id)
        .aexists()
    )


##########################################################
# list roles
##########################################################


async def list_roles(
    model: type[TR],
    filters: ProjectRoleFilters = {},
    offset: int | None = None,
    limit: int | None = None,
) -> list[TR]:
    qs = model.objects.all().filter(**filters)

    if limit is not None and offset is not None:
        limit += offset

    return [a async for a in qs[offset:limit]]


##########################################################
# get role
##########################################################


async def get_role(
    model: type[TR],
    filters: ProjectRoleFilters = {},
    select_related: ProjectRoleSelectRelated = ["project"],
) -> TR:
    qs = model.objects.all().filter(**filters).select_related(*select_related)
    return await qs.aget()


##########################################################
# update project role
##########################################################


async def update_role(role: TR, values: dict[str, Any] = {}) -> TR:
    for attr, value in values.items():
        setattr(role, attr, value)

    await role.asave()
    return role
