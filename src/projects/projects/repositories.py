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
from django.db.models import Case, Count, When

from base.utils.datetime import aware_utcnow
from base.utils.files import File
from commons.utils import transaction_atomic_async
from memberships.choices import InvitationStatus
from projects import references
from projects.memberships import repositories as memberships_repositories
from projects.projects.models import Project, ProjectTemplate
from users.models import User
from workflows import repositories as workflows_repositories
from workspaces.workspaces.models import Workspace

##########################################################
# Project - filters and querysets
##########################################################


class ProjectFilters(TypedDict, total=False):
    workspace_id: UUID
    invitations__user_id: UUID
    invitations__status: InvitationStatus
    memberships__user_id: UUID
    memberships__role__is_owner: bool


ProjectSelectRelated = list[Literal["workspace",]]

ProjectPrefetchRelated = list[Literal["workflows"]]

ProjectOrderBy = list[Literal["-created_at",]]


##########################################################
# Project - create project
##########################################################


async def create_project(
    workspace: Workspace,
    name: str,
    created_by: User,
    landing_page: str,
    description: str | None = None,
    color: int | None = None,
    logo: File | None = None,
) -> Project:
    project = Project(
        name=name,
        created_by=created_by,
        workspace=workspace,
        logo=logo,
        landing_page=landing_page,
    )
    if description:
        project.description = description
    if color:
        project.color = color

    await project.asave()

    return project


##########################################################
# Project - list projects
##########################################################


async def list_projects(
    filters: ProjectFilters = {},
    select_related: ProjectSelectRelated = [],
    prefetch_related: ProjectPrefetchRelated = [],
    order_by: ProjectOrderBy = ["-created_at"],
    offset: int | None = None,
    limit: int | None = None,
    num_owners: int | None = None,
    is_individual_project: bool | None = None,
) -> list[Project]:
    qs = Project.objects.all()
    if num_owners is not None:
        qs = qs.annotate(
            num_owners=Count(Case(When(memberships__role__is_owner=True, then=1)))
        ).filter(num_owners=num_owners)

    # filters for those projects where the user is the only project member
    if is_individual_project is not None:
        qs = qs.annotate(num_members=Count("members"))
        qs = (
            qs.filter(num_members=1)
            if is_individual_project
            else qs.filter(num_members__gt=1)
        )
    qs = (
        qs.filter(**filters)
        .select_related(*select_related)
        .prefetch_related(*prefetch_related)
        .order_by(*order_by)
        .distinct()
    )

    if limit is not None and offset is not None:
        limit += offset

    return [p async for p in qs[offset:limit]]


##########################################################
# Project - get project
##########################################################


async def get_project(
    project_id: UUID,
    select_related: ProjectSelectRelated = ["workspace"],
    prefetch_related: ProjectPrefetchRelated = [],
) -> Project | None:
    qs = (
        Project.objects.all()
        .select_related(*select_related)
        .prefetch_related(*prefetch_related)
    )

    try:
        return await qs.aget(id=project_id)
    except Project.DoesNotExist:
        return None


##########################################################
# Project - update project
##########################################################


async def update_project(project: Project, values: dict[str, Any] = {}) -> Project:
    for attr, value in values.items():
        setattr(project, attr, value)

    project.modified_at = aware_utcnow()
    await project.asave(update_fields=values.keys())
    return project


##########################################################
# delete project
##########################################################


@transaction_atomic_async
async def delete_projects(project_id: UUID) -> int:
    qs = Project.objects.all().filter(id=project_id)
    await sync_to_async(references.delete_project_references_sequences)(
        project_ids=[p_id async for p_id in qs.values_list("id", flat=True)]
    )
    count, _ = await qs.adelete()
    return count


##########################################################
# Project - misc
##########################################################


async def get_total_projects(
    workspace_id: UUID,
    filters: ProjectFilters = {},
) -> int:
    return await (
        Project.objects.all()
        .filter(workspace_id=workspace_id, **filters)
        .distinct()
        .acount()
    )


async def get_first_workflow_slug(project: Project) -> str | None:
    return await project.workflows.values_list("slug", flat=True).afirst()


##########################################################
# Project Template - filters and querysets
##########################################################


class ProjectTemplateFilters(TypedDict, total=False):
    slug: str


##########################################################
# Project Template - get project template
##########################################################


async def get_project_template(
    filters: ProjectTemplateFilters = {},
) -> ProjectTemplate | None:
    qs = ProjectTemplate.objects.all().filter(**filters)

    try:
        return await qs.aget()
    except ProjectTemplate.DoesNotExist:
        return None


##########################################################
# Project Template - misc
##########################################################


@transaction_atomic_async
async def apply_template_to_project(
    template: ProjectTemplate, project: Project
) -> None:
    for role in template.roles:
        await memberships_repositories.create_project_role(
            name=role["name"],
            slug=role["slug"],
            order=role["order"],
            project=project,
            permissions=role["permissions"],
            is_owner=role["is_owner"],
            editable=role["editable"],
        )

    for workflow in template.workflows:
        wf = await workflows_repositories.create_workflow(
            name=workflow["name"],
            order=workflow["order"],
            project=project,
        )
        for status in template.workflow_statuses:
            await workflows_repositories.create_workflow_status(
                name=status["name"],
                color=status["color"],
                order=status["order"],
                workflow=wf,
            )
