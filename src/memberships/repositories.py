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

from django.db.models import Count, F, Q, QuerySet

from base.db.utils import Q_for_related
from memberships.choices import InvitationStatus
from memberships.models import Invitation, Membership, Role
from projects.projects.models import Project
from users import repositories as users_repositories
from users.models import AnyUser, User
from workspaces.workspaces.models import Workspace

T = TypeVar("T", Project, Workspace)

##########################################################
# membership type
##########################################################

TOTAL_PROJECTS_IS_MEMBER_ANNOTATION = Count(
    "workspace__projects",
    filter=Q(workspace__projects__memberships__user_id=F("user_id")),
)


class _MembershipFilters(TypedDict, total=False):
    user__username: str
    user_id: UUID
    role__permissions__contains: list[str]


class ProjectMembershipFilters(_MembershipFilters, total=False):
    project_id: UUID
    project__workspace_id: UUID


class WorkspaceMembershipFilters(_MembershipFilters, total=False):
    workspace_id: UUID


MembershipFilters = ProjectMembershipFilters | WorkspaceMembershipFilters


class WorkspaceMembershipAnnotation(TypedDict, total=False):
    total_projects_is_member: type(TOTAL_PROJECTS_IS_MEMBER_ANNOTATION)


MembershipAnnotation = WorkspaceMembershipAnnotation

ProjectMembershipSelectRelated = list[
    Literal[
        "project",
        "role",
        "user",
    ]
    | None
]
WorkspaceMembershipSelectRelated = list[
    Literal[
        "workspace",
        "role",
        "user",
    ]
    | None
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

ProjectRoleSelectRelated = list[Literal["project",] | None]
WorkspaceRoleSelectRelated = list[Literal["workspace",] | None]
RoleSelectRelated = ProjectRoleSelectRelated | WorkspaceRoleSelectRelated

RoleOrderBy = list[Literal["order", "name"]]
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
    project__workspace_id: UUID


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
    | None
]
WorkspaceInvitationSelectRelated = list[
    Literal[
        "user",
        "role",
        "workspace",
        "invited_by",
    ]
    | None
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
    select_related: MembershipSelectRelated = [None],
    order_by: MembershipOrderBy = ["user__full_name"],
    annotations: MembershipAnnotation = {},
    offset: int | None = None,
    limit: int | None = None,
) -> list[TM]:
    qs = (
        model.objects.all()
        .filter(**filters)
        .select_related(*select_related)
        .order_by(*order_by)
        .annotate(**annotations)
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
    annotations: MembershipAnnotation = {},
) -> TM:
    qs = (
        model.objects.all()
        .filter(**filters)
        .select_related(*select_related)
        .annotate(**annotations)
    )
    return await qs.aget()


async def exists_membership(
    model: type[TM],
    filters: MembershipFilters = {},
) -> bool:
    qs = model.objects.all().filter(**filters)
    return await qs.aexists()


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


async def list_members(reference_object: T) -> list[User]:
    qs = reference_object.members.all()
    return [a async for a in qs]


def only_member_queryset(
    model: type[T],
    user: User,
) -> QuerySet[T]:
    """
    returns a queryset for all object where user is the only member
    """
    qs = model.objects.all()
    # add explicite order_by so it doesn't get removed by groupby implicit query in annotate
    qs = qs.order_by(*qs.query.order_by or model._meta.ordering)
    qs = qs.annotate(num_members=Count("members")).filter(num_members=1)
    qs = qs.filter(
        **{
            "memberships__user_id": user.id,
        }
    )
    return qs.distinct()


def only_owner_collective_queryset(model: type[T], user: User) -> QuerySet[T]:
    """
    returns a queryset for all projects where user is the only owner and other members exists
    """
    qs = model.objects.all()
    # add explicite order_by so it doesn't get removed by groupby implicit query in annotate
    qs = qs.order_by(*qs.query.order_by or model._meta.ordering)
    qs = qs.annotate(
        num_owners=Count("memberships", filter=Q(memberships__role__is_owner=True))
    ).filter(num_owners=1)
    qs = qs.annotate(num_members=Count("members")).filter(num_members__gt=1)
    qs = qs.filter(
        **{
            "memberships__user_id": user.id,
            "memberships__role__is_owner": True,
        }
    )
    return qs.distinct()


##########################################################
# list roles
##########################################################


async def list_roles(
    model: type[TR],
    filters: RoleFilters = {},
    order_by: RoleOrderBy = ["order", "name"],
    offset: int | None = None,
    limit: int | None = None,
    get_total_members=False,
) -> list[TR]:
    qs = model.objects.all().filter(**filters).order_by(*order_by)
    if get_total_members:
        qs = qs.annotate(total_members=Count("memberships"))

    if limit is not None and offset is not None:
        limit += offset

    return [a async for a in qs[offset:limit]]


##########################################################
# get role
##########################################################


async def get_role(
    model: type[TR],
    filters: RoleFilters = {},
    select_related: RoleSelectRelated = [None],
    get_total_members=False,
) -> TR:
    qs = model.objects.all().filter(**filters).select_related(*select_related)
    if get_total_members:
        qs = qs.annotate(total_members=Count("memberships"))
    return await qs.aget()


##########################################################
# update project role
##########################################################


async def update_role(role: TR, values: dict[str, Any] = {}) -> TR:
    # Prevent hitting the database with an empty PATCH
    if len(values) == 0:
        return role
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
    select_related: InvitationSelectRelated = [None],
    order_by: InvitationOrderBy = [],
    order_priorities: InvitationFilters = {},
) -> list[TI]:
    """
    order_priorities:
    use order_priorities to add possibility to priorise based on some conditions
    for exemple if order_priorities = {"status": PENDING, resent_at__ge: now()}
    this will result in the following queryset:
    qs.annotate(priority1=Q(status=PENDING), priority2=Q(resent_at__ge=now()).order_by("-priority1", "-priority2")
    """
    qs = model.objects.all().filter(**filters).select_related(*select_related)
    qs = qs.annotate(
        **{
            f"priority{i}": Q(**{priority_field: priority_value})
            for i, (priority_field, priority_value) in enumerate(
                order_priorities.items()
            )
        }
    )
    if order_by or order_priorities:
        # only replace default order_by if defined
        qs = qs.order_by(
            *(f"-priority{i}" for i in range(len(order_priorities))), *order_by
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
    select_related: InvitationSelectRelated = [None],
) -> TI:
    qs = model.objects.all().filter(**filters).select_related(*select_related)
    if q_filter:
        qs = qs.filter(q_filter)
    return await qs.aget()


async def exists_invitation(
    model: type[TI],
    filters: InvitationFilters = {},
    q_filter: Q | None = None,
) -> bool:
    qs = model.objects.all().filter(**filters)
    if q_filter:
        qs = qs.filter(q_filter)
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
# queries invitation
##########################################################


def pending_user_invitation_query(user: AnyUser) -> Q:
    by_user = Q(user_id=user.id)
    by_email = Q(user__isnull=True) & Q(email__iexact=user.email)
    return Q(status=InvitationStatus.PENDING) & (by_user | by_email)


def invitation_username_or_email_query(username_or_email: str) -> Q:
    by_user = Q_for_related(
        users_repositories.username_or_email_query(username_or_email), "user"
    )
    by_email = Q(user__isnull=True, email__iexact=username_or_email)
    return by_user | by_email
