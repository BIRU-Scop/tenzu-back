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

from itertools import chain
from typing import Any, Iterable, Literal
from uuid import UUID

from asgiref.sync import sync_to_async
from django.db.models import (
    CharField,
    Count,
    Exists,
    IntegerField,
    OuterRef,
    Prefetch,
    Q,
    Subquery,
    Value,
)
from django.db.models.functions import Coalesce

from base.utils.datetime import aware_utcnow
from projects.invitations.choices import ProjectInvitationStatus
from projects.projects.models import Project
from users.models import User
from workspaces.workspaces.models import Workspace

##########################################################
# filters and querysets
##########################################################


WorkspacePrefetchRelated = list[Literal["projects",]]


WorkspaceOrderBy = list[Literal["-created_at",]]


##########################################################
# create workspace
##########################################################


@sync_to_async
def create_workspace(name: str, color: int, created_by: User) -> Workspace:
    return Workspace.objects.create(name=name, color=color, created_by=created_by)


##########################################################
# list
##########################################################


async def list_workspaces(
    user: User,
    prefetch_related: WorkspacePrefetchRelated = [],
    order_by: WorkspaceOrderBy = ["-created_at"],
    has_projects: bool | None = None,
    is_only_user: bool = False,
) -> list[Workspace]:
    qs = Workspace.objects.all()
    if is_only_user:
        qs = qs.annotate(num_members=Count("members")).filter(num_members=1)
    if has_projects is not None:
        qs = qs.filter(~Q(projects=None) if has_projects else Q(projects=None))
    qs = (
        qs.filter(memberships__user_id=user.id)
        .prefetch_related(*prefetch_related)
        .order_by(*order_by)
        .distinct()
    )

    return [workspace async for workspace in qs]


@sync_to_async
def list_user_workspaces_overview(user: User) -> list[Workspace]:
    # workspaces where the user is ws-member with all its projects
    ws_member_ids = (
        Workspace.objects.filter(
            memberships__user_id=user.id,  # user_is_ws_member
        )
        .order_by("-created_at")
        .values_list("id", flat=True)
    )
    has_projects = Exists(Project.objects.filter(workspace=OuterRef("pk")))
    member_ws: Iterable[Workspace] = Workspace.objects.none()
    for ws_id in ws_member_ids:
        projects_ids = list(
            Project.objects.filter(workspace_id=ws_id)  # pj_in_workspace
            .order_by("-created_at")
            .values_list("id", flat=True)
        )
        total_projects = len(projects_ids)
        projects_qs = Project.objects.filter(id__in=projects_ids[:12]).order_by(
            "-created_at"
        )
        invited_projects_qs = Project.objects.filter(
            Q(invitations__user_id=user.id)
            | (
                Q(invitations__user__isnull=True)
                & Q(invitations__email__iexact=user.email)
            ),
            invitations__status=ProjectInvitationStatus.PENDING,
            workspace_id=ws_id,
        )
        qs = (
            Workspace.objects.filter(id=ws_id)
            .prefetch_related(
                Prefetch("projects", queryset=projects_qs, to_attr="latest_projects"),
                Prefetch(
                    "projects", queryset=invited_projects_qs, to_attr="invited_projects"
                ),
            )
            .annotate(total_projects=Value(total_projects, output_field=IntegerField()))
            .annotate(has_projects=has_projects)
            .annotate(user_role=Value("member", output_field=CharField()))
        )
        member_ws = chain(member_ws, qs)

    # workspaces where the user is ws-guest with all its visible projects
    # or is not even a guest and only have invited projects
    user_pj_member = Q(memberships__user__id=user.id)
    user_invited_pj = Q(invitations__status=ProjectInvitationStatus.PENDING) & (
        Q(invitations__user_id=user.id)
        | (Q(invitations__user__isnull=True) & Q(invitations__email__iexact=user.email))
    )
    guest_ws_ids = (
        Project.objects.filter(user_pj_member | user_invited_pj)
        .exclude(workspace__memberships__user__id=user.id)  # user_not_ws_member
        .order_by("workspace_id")
        .distinct("workspace_id")
        .values_list("workspace_id", flat=True)
    )

    guest_ws: Iterable[Workspace] = Workspace.objects.none()
    for ws_id in guest_ws_ids:
        projects_ids = list(
            Project.objects.filter(
                workspace_id=ws_id,  # pj_in_workspace,
                memberships__user__id=user.id,  # user_pj_member
            )
            .order_by("-created_at")
            .values_list("id", flat=True)
        )
        total_projects = len(projects_ids)
        projects_qs = Project.objects.filter(id__in=projects_ids[:12]).order_by(
            "-created_at"
        )
        invited_projects_qs = Project.objects.filter(
            Q(invitations__user_id=user.id)
            | (
                Q(invitations__user__isnull=True)
                & Q(invitations__email__iexact=user.email)
            ),
            invitations__status=ProjectInvitationStatus.PENDING,
            workspace_id=ws_id,
        )
        qs = (
            Workspace.objects.filter(id=ws_id)
            .prefetch_related(
                Prefetch("projects", queryset=projects_qs, to_attr="latest_projects"),
                Prefetch(
                    "projects", queryset=invited_projects_qs, to_attr="invited_projects"
                ),
            )
            .annotate(total_projects=Value(total_projects, output_field=IntegerField()))
            .annotate(has_projects=has_projects)
            .annotate(user_role=Value("guest", output_field=CharField()))
        )
        guest_ws = chain(guest_ws, qs)

    result = list(chain(member_ws, member_ws, guest_ws))
    return result


##########################################################
#  get workspace
##########################################################


@sync_to_async
def get_workspace(
    workspace_id: UUID,
) -> Workspace | None:
    qs = Workspace.objects.all().filter(id=workspace_id)
    try:
        return qs.get()
    except Workspace.DoesNotExist:
        return None


async def get_workspace_detail(
    user_id: UUID | None, workspace_id: UUID
) -> Workspace | None:
    # TODO user_id should probably be used to filter projects using membership
    qs = (
        Workspace.objects.all()
        .filter(id=workspace_id)
        .annotate(has_projects=Exists(Project.objects.filter(workspace=OuterRef("pk"))))
    )

    try:
        return await qs.aget()
    except Workspace.DoesNotExist:
        return None


async def get_workspace_summary(workspace_id: UUID) -> Workspace | None:
    qs = Workspace.objects.all().filter(id=workspace_id)
    try:
        return await qs.aget()
    except Workspace.DoesNotExist:
        return None


async def get_user_workspace_overview(user: User, id: UUID) -> Workspace | None:
    # Generic annotations:
    has_projects = Exists(Project.objects.filter(workspace=OuterRef("pk")))

    # Generic prefetch
    invited_projects_qs = Project.objects.filter(
        invitations__user_id=user.id,
        invitations__status=ProjectInvitationStatus.PENDING,
    )

    # workspaces where the user is member
    try:
        total_projects: Subquery | Count = Count("projects")
        visible_project_ids_qs = (
            Project.objects.filter(workspace=OuterRef("workspace"))
            .values_list("id", flat=True)
            .order_by("-created_at")
        )
        latest_projects_qs = Project.objects.filter(
            id__in=Subquery(visible_project_ids_qs[:12])
        ).order_by("-created_at")
        return await (
            Workspace.objects.filter(
                id=id,
                memberships__user_id=user.id,  # user_is_ws_member
            )
            .prefetch_related(
                Prefetch(
                    "projects", queryset=latest_projects_qs, to_attr="latest_projects"
                ),
                Prefetch(
                    "projects", queryset=invited_projects_qs, to_attr="invited_projects"
                ),
            )
            .annotate(total_projects=Coalesce(total_projects, 0))
            .annotate(has_projects=has_projects)
            .annotate(user_role=Value("member", output_field=CharField()))
            .aget()
        )
    except Workspace.DoesNotExist:
        pass  # The workspace selected is not of this kind

    # workspaces where the user is ws-guest with all its visible projects
    # or is not even a guest and only have invited projects
    try:
        user_not_ws_member = ~Q(members__id=user.id)
        user_pj_member = Q(projects__members__id=user.id)
        user_invited_pj = Q(
            projects__invitations__status=ProjectInvitationStatus.PENDING,
            projects__invitations__user_id=user.id,
        )
        total_projects = Subquery(
            Project.objects.filter(
                Q(workspace_id=OuterRef("id")),
                members__id=user.id,
            )
            .values("workspace")
            .annotate(count=Count("*"))
            .values("count"),
            output_field=IntegerField(),
        )
        visible_project_ids_qs = (
            Project.objects.filter(
                Q(workspace=OuterRef("workspace")),
                members__id=user.id,
            )
            .order_by("-created_at")
            .values_list("id", flat=True)
        )
        latest_projects_qs = Project.objects.filter(
            id__in=Subquery(visible_project_ids_qs[:12])
        ).order_by("-created_at")
        return await (
            Workspace.objects.filter(
                user_not_ws_member & (user_pj_member | user_invited_pj), id=id
            )
            .distinct()
            .prefetch_related(
                Prefetch(
                    "projects", queryset=latest_projects_qs, to_attr="latest_projects"
                ),
                Prefetch(
                    "projects", queryset=invited_projects_qs, to_attr="invited_projects"
                ),
            )
            .annotate(total_projects=Coalesce(total_projects, 0))
            .annotate(has_projects=has_projects)
            .annotate(user_role=Value("guest", output_field=CharField()))
            .aget()
        )
    except Workspace.DoesNotExist:
        return None  # There is no workspace with this id for this user


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


##########################################################
# misc
##########################################################


async def list_workspace_projects(workspace: Workspace) -> list[Project]:
    return [
        project async for project in workspace.projects.all().order_by("-created_at")
    ]
