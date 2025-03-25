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
from django.db.models import Q

from projects.invitations.choices import ProjectInvitationStatus
from projects.invitations.models import ProjectInvitation
from users.models import User

##########################################################
# filters and querysets
##########################################################


class ProjectInvitationFilters(TypedDict, total=False):
    id: UUID
    user: User
    email: str
    project_id: UUID
    status: ProjectInvitationStatus
    status__in: list[ProjectInvitationStatus]


def username_or_email_query(username_or_email: str) -> Q:
    by_user = Q(user__username__iexact=username_or_email) | Q(
        user__email__iexact=username_or_email
    )
    by_email = Q(user__isnull=True, email__iexact=username_or_email)
    return by_user | by_email


ProjectInvitationSelectRelated = list[
    Literal[
        "user",
        "project",
        "role",
        "project__workspace",
        "invited_by",
    ]
]


ProjectInvitationOrderBy = list[
    Literal[
        "user__full_name",
        "email",
    ]
]


##########################################################
# create project invitation
##########################################################


async def create_project_invitations(
    objs: list[ProjectInvitation],
    select_related: ProjectInvitationSelectRelated = ["user", "project", "role"],
) -> list[ProjectInvitation]:
    qs = ProjectInvitation.objects.all().select_related(*select_related)
    return await qs.abulk_create(objs=objs)


##########################################################
# list project invitations
##########################################################


async def list_project_invitations(
    filters: ProjectInvitationFilters = {},
    offset: int | None = None,
    limit: int | None = None,
    select_related: ProjectInvitationSelectRelated = ["project", "user", "role"],
    order_by: ProjectInvitationOrderBy = ["user__full_name", "email"],
) -> list[ProjectInvitation]:
    qs = (
        ProjectInvitation.objects.all()
        .filter(**filters)
        .select_related(*select_related)
        .order_by(*order_by)
    )

    if limit is not None and offset is not None:
        limit += offset

    return [a async for a in qs[offset:limit]]


##########################################################
# get project invitation
##########################################################


async def get_project_invitation(
    filters: ProjectInvitationFilters = {},
    q_filter: Q | None = None,
    select_related: ProjectInvitationSelectRelated = ["user", "project", "role"],
) -> ProjectInvitation | None:
    qs = (
        ProjectInvitation.objects.all()
        .filter(**filters)
        .select_related(*select_related)
    )
    if q_filter:
        qs = qs.filter(q_filter)
    try:
        return await qs.aget()
    except ProjectInvitation.DoesNotExist:
        return None


async def exist_project_invitation(
    filters: ProjectInvitationFilters = {},
) -> bool:
    qs = ProjectInvitation.objects.all().filter(**filters)
    return await qs.aexists()


##########################################################
# update project invitations
##########################################################


async def update_project_invitation(
    invitation: ProjectInvitation, values: dict[str, Any]
) -> ProjectInvitation:
    for attr, value in values.items():
        setattr(invitation, attr, value)

    await invitation.asave()
    return invitation


async def bulk_update_project_invitations(
    objs_to_update: list[ProjectInvitation], fields_to_update: list[str]
) -> None:
    await ProjectInvitation.objects.abulk_update(objs_to_update, fields_to_update)


async def update_user_projects_invitations(user: User) -> None:
    await ProjectInvitation.objects.filter(email=user.email).aupdate(user=user)


##########################################################
# delete project invitation
##########################################################


async def delete_project_invitation(
    filters: ProjectInvitationFilters = {},
    q_filter: Q | None = None,
) -> int:
    qs = ProjectInvitation.objects.all().filter(**filters)
    if q_filter:
        qs = qs.filter(q_filter)
    count, _ = await qs.adelete()
    return count
