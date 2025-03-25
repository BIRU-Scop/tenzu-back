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

from django.db.models import Q

from users.models import User
from workspaces.invitations.choices import WorkspaceInvitationStatus
from workspaces.invitations.models import WorkspaceInvitation

##########################################################
# filters and querysets
##########################################################


class WorkspaceInvitationFilters(TypedDict, total=False):
    id: UUID
    username_or_email: str
    user: User
    email: str
    workspace_id: UUID
    status: WorkspaceInvitationStatus
    status__in: list[WorkspaceInvitationStatus]


def username_or_email_query(username_or_email: str) -> Q:
    by_user = Q(user__username__iexact=username_or_email) | Q(
        user__email__iexact=username_or_email
    )
    by_email = Q(user__isnull=True, email__iexact=username_or_email)
    return by_user | by_email


WorkspaceInvitationSelectRelated = list[
    Literal[
        "user",
        "workspace",
        "invited_by",
    ]
]


WorkspaceInvitationOrderBy = list[
    Literal[
        "user__full_name",
        "email",
    ]
]


##########################################################
# create workspace invitations
##########################################################


async def create_workspace_invitations(
    objs: list[WorkspaceInvitation],
    select_related: WorkspaceInvitationSelectRelated = [],
) -> list[WorkspaceInvitation]:
    qs = WorkspaceInvitation.objects.all().select_related(*select_related)
    return await qs.abulk_create(objs=objs)


##########################################################
# list workspace invitations
##########################################################


async def list_workspace_invitations(
    filters: WorkspaceInvitationFilters = {},
    offset: int | None = None,
    limit: int | None = None,
    select_related: WorkspaceInvitationSelectRelated = [],
    order_by: WorkspaceInvitationOrderBy = ["user__full_name", "email"],
) -> list[WorkspaceInvitation]:
    qs = (
        WorkspaceInvitation.objects.all()
        .filter(**filters)
        .select_related(*select_related)
        .order_by(*order_by)
    )

    if limit is not None and offset is not None:
        limit += offset

    return [a async for a in qs[offset:limit]]


##########################################################
# get workspace invitation
##########################################################


async def get_workspace_invitation(
    filters: WorkspaceInvitationFilters = {},
    q_filter: Q | None = None,
    select_related: WorkspaceInvitationSelectRelated = [],
) -> WorkspaceInvitation | None:
    qs = (
        WorkspaceInvitation.objects.all()
        .filter(**filters)
        .select_related(*select_related)
    )
    try:
        return await qs.aget()
    except WorkspaceInvitation.DoesNotExist:
        return None


async def exist_workspace_invitation(
    filters: WorkspaceInvitationFilters = {},
) -> bool:
    qs = WorkspaceInvitation.objects.all().filter(**filters)
    return await qs.aexists()


##########################################################
# update workspace invitations
##########################################################


async def update_workspace_invitation(
    invitation: WorkspaceInvitation, values: dict[str, Any]
) -> WorkspaceInvitation:
    for attr, value in values.items():
        setattr(invitation, attr, value)

    await invitation.asave()
    return invitation


async def bulk_update_workspace_invitations(
    objs_to_update: list[WorkspaceInvitation], fields_to_update: list[str]
) -> None:
    await WorkspaceInvitation.objects.abulk_update(objs_to_update, fields_to_update)


async def update_user_workspaces_invitations(user: User) -> None:
    await WorkspaceInvitation.objects.filter(email=user.email).aupdate(user=user)


##########################################################
# delete workspace invitation
##########################################################


async def delete_workspace_invitation(
    filters: WorkspaceInvitationFilters = {},
    q_filter: Q | None = None,
) -> int:
    qs = WorkspaceInvitation.objects.all().filter(**filters)
    if q_filter:
        qs = qs.filter(q_filter)
    count, _ = await qs.adelete()
    return count
