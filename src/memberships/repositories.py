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

from django.db.models import Q

from memberships.choices import InvitationStatus
from memberships.models import Invitation, Membership, Role
from projects.projects.models import Project
from users.models import User
from workspaces.workspaces.models import Workspace

##########################################################
# membership type
##########################################################


class _MembershipFilters(TypedDict, total=False):
    user__username: str
    user_id: UUID
    role__permissions__contains: list[str]


class ProjectMembershipFilters(_MembershipFilters, total=False):
    project_id: UUID


class WorkspaceMembershipFilters(_MembershipFilters, total=False):
    workspace_id: UUID


MembershipFilters = ProjectMembershipFilters | WorkspaceMembershipFilters

ProjectMembershipSelectRelated = list[
    Literal[
        "project",
        "role",
        "user",
    ]
]
WorkspaceMembershipSelectRelated = list[
    Literal[
        "workspace",
        "role",
        "user",
    ]
]
MembershipSelectRelated = (
    ProjectMembershipSelectRelated | WorkspaceMembershipSelectRelated
)

MembershipOrderBy = list[Literal["user__full_name",]]
TM = TypeVar("TM", bound=Membership)


##########################################################
# role type
##########################################################


class _RoleFilters(TypedDict, total=False):
    slug: str
    memberships__user_id: UUID


class ProjectRoleFilters(_RoleFilters, total=False):
    project_id: UUID


class WorkspaceRoleFilters(_RoleFilters, total=False):
    workspace_id: UUID


RoleFilters = ProjectRoleFilters | WorkspaceRoleFilters

ProjectRoleSelectRelated = list[Literal["project",]]
WorkspaceRoleSelectRelated = list[Literal["workspace",]]
RoleSelectRelated = ProjectRoleSelectRelated | WorkspaceRoleSelectRelated
TR = TypeVar("TR", bound=Role)

##########################################################
# invitation type
##########################################################


class _InvitationFilters(TypedDict, total=False):
    id: UUID
    user: User
    email: str
    status: InvitationStatus
    status__in: list[InvitationStatus]


class ProjectInvitationFilters(_InvitationFilters, total=False):
    project_id: UUID


class WorkspaceInvitationFilters(_InvitationFilters, total=False):
    workspace_id: UUID


InvitationFilters = ProjectInvitationFilters | WorkspaceInvitationFilters


ProjectInvitationSelectRelated = list[
    Literal[
        "user",
        "project",
        "role",
        "project__workspace",
        "invited_by",
    ]
]
WorkspaceInvitationSelectRelated = list[
    Literal[
        "user",
        "role",
        "workspace",
        "invited_by",
    ]
]
InvitationSelectRelated = (
    ProjectInvitationSelectRelated | WorkspaceInvitationSelectRelated
)

InvitationOrderBy = list[
    Literal[
        "user__full_name",
        "email",
    ]
]
TI = TypeVar("TI", bound=Invitation)

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


async def has_other_owner_memberships(membership: TM):
    return (
        await membership.__class__.objects.all()
        .filter(role__is_owner=True, **membership.reference_model_filter)
        .exclude(id=membership.id)
        .aexists()
    )


async def list_members(
    reference_object: Project | Workspace, exclude_user=None
) -> list[User]:
    qs = reference_object.members.all()
    if exclude_user is not None:
        qs = qs.exclude(id=exclude_user.id)
    return [a async for a in qs]


##########################################################
# list roles
##########################################################


async def list_roles(
    model: type[TR],
    filters: RoleFilters = {},
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
    filters: RoleFilters = {},
    select_related: RoleSelectRelated = [],
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


##########################################################
# create invitations
##########################################################


async def create_invitations(
    model: type[TI],
    objs: list[TI],
) -> list[TI]:
    return await model.objects.abulk_create(objs=objs)


##########################################################
# list invitations
##########################################################


async def list_invitations(
    model: type[TI],
    filters: InvitationFilters = {},
    offset: int | None = None,
    limit: int | None = None,
    select_related: InvitationSelectRelated = [],
    order_by: InvitationOrderBy = ["user__full_name", "email"],
) -> list[TI]:
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
# get invitation
##########################################################


async def get_invitation(
    model: type[TI],
    filters: InvitationFilters = {},
    q_filter: Q | None = None,
    select_related: InvitationSelectRelated = [],
) -> TI:
    qs = model.objects.all().filter(**filters).select_related(*select_related)
    if q_filter:
        qs = qs.filter(q_filter)
    return await qs.aget()


async def exists_invitation(
    model: type[TI],
    filters: InvitationFilters = {},
) -> bool:
    qs = model.objects.all().filter(**filters)
    return await qs.aexists()


##########################################################
# update invitations
##########################################################


async def update_invitation(invitation: TI, values: dict[str, Any]) -> TI:
    for attr, value in values.items():
        setattr(invitation, attr, value)

    await invitation.asave()
    return invitation


async def bulk_update_invitations(
    model: type[TI], objs_to_update: list[TI], fields_to_update: list[str]
) -> None:
    await model.objects.abulk_update(objs_to_update, fields_to_update)


async def update_user_invitations(model: type[TI], user: User) -> None:
    await model.objects.filter(email=user.email).aupdate(user=user)


##########################################################
# delete invitation
##########################################################


async def delete_invitation(
    model: type[TI],
    filters: InvitationFilters = {},
    q_filter: Q | None = None,
) -> int:
    qs = model.objects.all().filter(**filters)
    if q_filter:
        qs = qs.filter(q_filter)
    count, _ = await qs.adelete()
    return count


##########################################################
# misc invitation
##########################################################


def username_or_email_query(username_or_email: str) -> Q:
    by_user = Q(user__username__iexact=username_or_email) | Q(
        user__email__iexact=username_or_email
    )
    by_email = Q(user__isnull=True, email__iexact=username_or_email)
    return by_user | by_email
