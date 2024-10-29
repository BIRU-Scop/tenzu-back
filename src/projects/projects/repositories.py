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

from base.db.models import Case, Count, QuerySet, When
from base.utils.datetime import aware_utcnow
from base.utils.files import File
from projects import references
from projects.invitations.choices import ProjectInvitationStatus
from projects.projects.models import Project, ProjectTemplate
from projects.roles import repositories as pj_roles_repositories
from users.models import User
from workflows import repositories as workflows_repositories
from workspaces.workspaces.models import Workspace

##########################################################
# Project - filters and querysets
##########################################################

DEFAULT_QUERYSET = Project.objects.all()


class ProjectFilters(TypedDict, total=False):
    id: UUID
    workspace_id: UUID
    invitee_id: UUID
    invitation_status: ProjectInvitationStatus
    project_member_id: UUID
    is_admin: bool
    num_admins: int
    is_onewoman_project: bool


def _apply_filters_to_project_queryset(
    qs: QuerySet[Project],
    filters: ProjectFilters = {},
) -> QuerySet[Project]:
    filter_data = dict(filters.copy())

    if "invitation_status" in filter_data:
        filter_data["invitations__status"] = filter_data.pop("invitation_status")

    if "invitee_id" in filter_data:
        filter_data["invitations__user_id"] = filter_data.pop("invitee_id")

    # filters for those projects where the user is already a project member
    if "project_member_id" in filter_data:
        filter_data["memberships__user_id"] = filter_data.pop("project_member_id")

    if "is_admin" in filter_data:
        filter_data["memberships__role__is_admin"] = filter_data.pop("is_admin")

    if "num_admins" in filter_data:
        qs = qs.annotate(num_admins=Count(Case(When(memberships__role__is_admin=True, then=1))))

    # filters for those projects where the user is the only project member
    if "is_onewoman_project" in filter_data:
        qs = qs.annotate(num_members=Count("members"))
        if filter_data.pop("is_onewoman_project"):
            filter_data["num_members"] = 1
        else:
            filter_data["num_members__gt"] = 1

    return qs.filter(**filter_data)


ProjectSelectRelated = list[Literal["workspace",]]


def _apply_select_related_to_project_queryset(
    qs: QuerySet[Project],
    select_related: ProjectSelectRelated,
) -> QuerySet[Project]:
    return qs.select_related(*select_related)


ProjectPrefetchRelated = list[Literal["workflows"]]


def _apply_prefetch_related_to_project_queryset(
    qs: QuerySet[Project],
    prefetch_related: ProjectPrefetchRelated,
) -> QuerySet[Project]:
    return qs.prefetch_related(*prefetch_related)


ProjectOrderBy = list[Literal["-created_at",]]


def _apply_order_by_to_project_queryset(
    qs: QuerySet[Project],
    order_by: ProjectOrderBy,
) -> QuerySet[Project]:
    return qs.order_by(*order_by)


##########################################################
# Project - create project
##########################################################


@sync_to_async
def create_project(
    workspace: Workspace,
    name: str,
    created_by: User,
    description: str | None = None,
    color: int | None = None,
    logo: File | None = None,
) -> Project:
    project = Project(
        name=name,
        created_by=created_by,
        workspace=workspace,
        logo=logo,
    )
    if description:
        project.description = description
    if color:
        project.color = color

    project.save()

    return project


##########################################################
# Project - list projects
##########################################################


@sync_to_async
def list_projects(
    filters: ProjectFilters = {},
    select_related: ProjectSelectRelated = [],
    prefetch_related: ProjectPrefetchRelated = [],
    order_by: ProjectOrderBy = ["-created_at"],
    offset: int | None = None,
    limit: int | None = None,
) -> list[Project]:
    qs = _apply_filters_to_project_queryset(qs=DEFAULT_QUERYSET, filters=filters)
    qs = _apply_select_related_to_project_queryset(qs=qs, select_related=select_related)
    qs = _apply_prefetch_related_to_project_queryset(qs=qs, prefetch_related=prefetch_related)
    qs = _apply_order_by_to_project_queryset(order_by=order_by, qs=qs)
    qs = qs.distinct()

    if limit is not None and offset is not None:
        limit += offset

    return list(qs[offset:limit])


##########################################################
# Project - get project
##########################################################


@sync_to_async
def get_project(
    filters: ProjectFilters = {},
    select_related: ProjectSelectRelated = ["workspace"],
    prefetch_related: ProjectPrefetchRelated = [],
) -> Project | None:
    qs = _apply_filters_to_project_queryset(qs=DEFAULT_QUERYSET, filters=filters)
    qs = _apply_select_related_to_project_queryset(qs=qs, select_related=select_related)
    qs = _apply_prefetch_related_to_project_queryset(qs=qs, prefetch_related=prefetch_related)

    try:
        return qs.get()
    except Project.DoesNotExist:
        return None


##########################################################
# Project - update project
##########################################################


@sync_to_async
def update_project(project: Project, values: dict[str, Any] = {}) -> Project:
    for attr, value in values.items():
        setattr(project, attr, value)

    project.modified_at = aware_utcnow()
    project.save()
    return project


##########################################################
# delete project
##########################################################


@sync_to_async
def delete_projects(filters: ProjectFilters = {}) -> int:
    qs = _apply_filters_to_project_queryset(qs=DEFAULT_QUERYSET, filters=filters)
    references.delete_project_references_sequences(project_ids=list(qs.values_list("id", flat=True)))
    count, _ = qs.delete()
    return count


##########################################################
# Project - misc
##########################################################


@sync_to_async
def get_total_projects(
    filters: ProjectFilters = {},
) -> int:
    qs = _apply_filters_to_project_queryset(filters=filters, qs=DEFAULT_QUERYSET)
    return qs.distinct().count()


##########################################################
# Project Template - filters and querysets
##########################################################


DEFAULT_PROJECT_TEMPLATE_QUERYSET = ProjectTemplate.objects.all()


class ProjectTemplateFilters(TypedDict, total=False):
    slug: str


def _apply_filters_to_project_template_queryset(
    qs: QuerySet[ProjectTemplate],
    filters: ProjectTemplateFilters = {},
) -> QuerySet[ProjectTemplate]:
    return qs.filter(**filters)


##########################################################
# Project Template - get project template
##########################################################


@sync_to_async
def get_project_template(
    filters: ProjectTemplateFilters = {},
) -> ProjectTemplate | None:
    qs = _apply_filters_to_project_template_queryset(qs=DEFAULT_PROJECT_TEMPLATE_QUERYSET, filters=filters)

    try:
        return qs.get()
    except ProjectTemplate.DoesNotExist:
        return None


##########################################################
# Project Template - misc
##########################################################


def apply_template_to_project_sync(template: ProjectTemplate, project: Project) -> None:
    for role in template.roles:
        pj_roles_repositories.create_project_role_sync(
            name=role["name"],
            slug=role["slug"],
            order=role["order"],
            project=project,
            permissions=role["permissions"],
            is_admin=role["is_admin"],
        )

    for workflow in template.workflows:
        wf = workflows_repositories.create_workflow_sync(
            name=workflow["name"],
            slug=workflow["slug"],
            order=workflow["order"],
            project=project,
        )
        for status in template.workflow_statuses:
            workflows_repositories.create_workflow_status_sync(
                name=status["name"],
                color=status["color"],
                order=status["order"],
                workflow=wf,
            )


apply_template_to_project = sync_to_async(apply_template_to_project_sync)
