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
from django.db.models import Exists, OuterRef, Q

from base.db.utils import Q_for_related
from base.utils.datetime import aware_utcnow
from base.utils.files import File
from commons.utils import transaction_atomic_async
from memberships import repositories as memberships_repositories
from memberships.choices import InvitationStatus
from projects import references
from projects.invitations.models import ProjectInvitation
from projects.memberships import repositories as pj_memberships_repositories
from projects.memberships.models import ProjectRole
from projects.projects.models import Project, ProjectTemplate
from users.models import User
from workflows import repositories as workflows_repositories
from workflows.models import Workflow, WorkflowStatus
from workspaces.workspaces.models import Workspace

##########################################################
# Project - filters and querysets
##########################################################


class ProjectFilters(TypedDict, total=False):
    workspace_id: UUID
    workspace__in: list[Workspace]
    invitations__user_id: UUID
    invitations__status: InvitationStatus
    memberships__user_id: UUID
    memberships__role__is_owner: bool


ProjectSelectRelated = list[Literal["workspace",] | None]

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


async def list_workspace_projects_for_user(
    workspace: Workspace, user: User
) -> list[Project]:
    # search user in workspace or project queryset through their invitations
    user_invited_query = Q_for_related(
        memberships_repositories.pending_user_invitation_query(user), "invitations"
    )
    # search user in workspace or project queryset through their membership
    user_member_query = Q(memberships__user_id=user.id)

    qs = (
        Project.objects.filter(
            user_invited_query | user_member_query,
            workspace=workspace,
        )
        .annotate(
            user_is_invited=Exists(
                ProjectInvitation.objects.filter(
                    memberships_repositories.pending_user_invitation_query(user),
                    project_id=OuterRef("pk"),
                )
            ),
        )
        .distinct()
        .order_by("-user_is_invited", "-created_at")
    )

    return [pj async for pj in qs]


##########################################################
# Project - get project
##########################################################


async def get_project(
    project_id: UUID,
    select_related: ProjectSelectRelated = ["workspace"],
    prefetch_related: ProjectPrefetchRelated = [],
) -> Project:
    qs = (
        Project.objects.all()
        .select_related(*select_related)
        .prefetch_related(*prefetch_related)
    )

    return await qs.aget(id=project_id)


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

    return await qs.aget()


##########################################################
# Project Template - misc
##########################################################


@transaction_atomic_async
async def apply_template_to_project(
    template: ProjectTemplate, project: Project
) -> list[ProjectRole]:
    roles = await pj_memberships_repositories.bulk_create_project_roles(
        [
            ProjectRole(
                name=role["name"],
                order=role["order"],
                slug=role["slug"],
                project=project,
                permissions=role["permissions"],
                is_owner=role["is_owner"],
                editable=role["editable"],
            )
            for role in template.roles
        ]
    )

    workflows = await workflows_repositories.bulk_create_workflows(
        [
            Workflow(
                name=workflow["name"],
                slug=workflow["slug"],
                order=workflow["order"],
                project=project,
            )
            for workflow in template.workflows
        ]
    )
    await workflows_repositories.bulk_create_workflow_statuses(
        [
            WorkflowStatus(
                name=status["name"],
                color=status["color"],
                order=status["order"],
                workflow=wf,
            )
            for status in template.workflow_statuses
            for wf in workflows
        ]
    )
    # do not return workflows, they can't be used as-is
    # because statuses are created separately so they're not put in prefetched_cache
    return roles
