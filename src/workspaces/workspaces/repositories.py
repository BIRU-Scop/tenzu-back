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

from typing import Any, Literal
from uuid import UUID

from django.db.models import (
    Exists,
    OuterRef,
    Prefetch,
    Q,
)
from django.db.models.aggregates import Count

from base.db.utils import Q_for_related
from base.utils.datetime import aware_utcnow
from memberships import repositories as memberships_repositories
from projects.projects.models import Project
from users.models import User
from workspaces.invitations.models import WorkspaceInvitation
from workspaces.memberships.models import WorkspaceMembership
from workspaces.workspaces.models import Workspace

##########################################################
# filters and querysets
##########################################################

PROJECT_PREFETCH = Prefetch(
    "projects", queryset=Project.objects.order_by("-created_at")
)


WorkspacePrefetchRelated = list[PROJECT_PREFETCH]


WorkspaceOrderBy = list[Literal["-created_at",]]


##########################################################
# create workspace
##########################################################


async def create_workspace(name: str, color: int, created_by: User) -> Workspace:
    return await Workspace.objects.acreate(
        name=name, color=color, created_by=created_by
    )


##########################################################
# list
##########################################################


async def list_user_workspaces_overview(user: User) -> list[Workspace]:
    # --- Utility queries and querysets
    #####
    ### QUERIES
    # search user in invitation query
    pending_user_invitation_query = (
        memberships_repositories.pending_user_invitation_query(user)
    )
    # search user in workspace or project queryset through their invitations
    user_invited_query = Q_for_related(pending_user_invitation_query, "invitations")
    # search user in workspace queryset through their projects' invitations
    user_pj_in_ws_invited_query = Q_for_related(user_invited_query, "projects")
    ### QUERYSETS
    # queryset for projects where user is member
    member_projects_qs = (
        Project.objects.filter(
            memberships__user_id=user.id,
        )
        .distinct()
        .order_by("-created_at")
    )
    # queryset for projects where user is invited
    invited_projects_qs = (
        Project.objects.filter(user_invited_query).distinct().order_by("-created_at")
    )
    #####

    # queryset for all workspaces where user is member or invited
    # (either directly to workspace or to one of its projects)
    ws_qs = (
        Workspace.objects.filter(
            Q(memberships__user_id=user.id)
            | user_invited_query
            | user_pj_in_ws_invited_query
        )
        .annotate(
            user_is_invited=Exists(
                WorkspaceInvitation.objects.filter(
                    pending_user_invitation_query, workspace_id=OuterRef("pk")
                )
            ),
            user_is_member=Exists(
                WorkspaceMembership.objects.filter(
                    user_id=user.id, workspace_id=OuterRef("pk")
                )
            ),
        )
        .prefetch_related(
            Prefetch(
                "projects", queryset=member_projects_qs, to_attr="user_member_projects"
            ),
            Prefetch(
                "projects",
                queryset=invited_projects_qs,
                to_attr="user_invited_projects",
            ),
        )
        .order_by("user_is_member", "-created_at")
        .distinct()
    )

    return [ws async for ws in ws_qs]


##########################################################
#  get workspace
##########################################################


async def get_workspace(workspace_id: UUID, get_total_project=False) -> Workspace:
    qs = Workspace.objects.all()
    if get_total_project:
        qs = qs.annotate(total_projects=Count("projects"))
    return await qs.aget(id=workspace_id)


##########################################################
# update workspace
##########################################################


async def update_workspace(
    workspace: Workspace, values: dict[str, Any] = {}
) -> Workspace:
    for attr, value in values.items():
        setattr(workspace, attr, value)

    workspace.modified_at = aware_utcnow()
    await workspace.asave()
    return workspace


##########################################################
# delete workspace
##########################################################


async def delete_workspace(workspace_id: UUID) -> int:
    qs = Workspace.objects.all().filter(id=workspace_id)
    count, _ = await qs.adelete()
    return count
