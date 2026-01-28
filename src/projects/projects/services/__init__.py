# -*- coding: utf-8 -*-
# Copyright (C) 2024-2026 BIRU
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

from typing import Any
from uuid import UUID

from django.conf import settings
from django.db.models.fields.files import FieldFile
from easy_thumbnails.files import ThumbnailFile
from ninja import UploadedFile

from base.utils.images import ImageSizeFormat, get_thumbnail
from commons.utils import (
    get_absolute_url,
    transaction_atomic_async,
    transaction_on_commit_async,
)
from permissions.choices import ProjectPermissions
from projects.memberships import repositories as memberships_repositories
from projects.projects import events as projects_events
from projects.projects import repositories as projects_repositories
from projects.projects import tasks as projects_tasks
from projects.projects.models import Project, ProjectTemplate
from projects.projects.serializers import (
    ProjectDetailSerializer,
)
from users.models import AnyUser, User
from workflows import repositories as workflows_repositories
from workspaces.workspaces.models import Workspace


def get_landing_page_for_workflow(slug: str | None):
    return f"kanban/{slug}" if slug else ""


##########################################################
# create project
##########################################################


async def create_project(
    workspace: Workspace,
    name: str,
    created_by: User,
    description: str | None,
    color: int | None,
    logo: UploadedFile | None = None,
) -> ProjectDetailSerializer:
    project = await _create_project(
        workspace=workspace,
        name=name,
        created_by=created_by,
        description=description,
        color=color,
        logo_file=logo,
    )
    return await get_project_detail(project=project, user=created_by)


@transaction_atomic_async
async def _create_project(
    workspace: Workspace,
    name: str,
    created_by: User,
    description: str | None,
    color: int | None,
    logo_file: UploadedFile | None = None,
) -> Project:
    """
    Create project and set user cache property for role
    """
    try:
        template = await projects_repositories.get_project_template(
            filters={"slug": settings.DEFAULT_PROJECT_TEMPLATE}
        )
    except ProjectTemplate.DoesNotExist as e:
        raise Exception(
            f"Default project template '{settings.DEFAULT_PROJECT_TEMPLATE}' not found. "
            "Try to run migrations again and check if the error persist."
        ) from e

    landing_page = (
        get_landing_page_for_workflow(template.workflows[0]["slug"])
        if template and template.workflows
        else ""
    )

    project = await projects_repositories.create_project(
        workspace=workspace,
        name=name,
        created_by=created_by,
        description=description,
        color=color,
        logo=logo_file,
        landing_page=landing_page,
    )

    roles = await projects_repositories.apply_template_to_project(
        template=template, project=project
    )
    try:
        owner_role = [role for role in roles if role.is_owner][0]
    except IndexError as e:
        raise Exception(
            "Default project template does not have a owner role. "
            "Try to load fixtures again and check if the error persist."
        ) from e
    await memberships_repositories.create_project_membership(
        user=created_by, project=project, role=owner_role
    )
    created_by.project_role = owner_role

    project.user_is_invited = False
    await transaction_on_commit_async(
        projects_events.emit_event_when_project_is_created
    )(project=project)

    return project


##########################################################
# list projects
##########################################################


async def list_workspace_projects_for_user(
    workspace: Workspace, user: User
) -> list[Project]:
    return await projects_repositories.list_workspace_projects_for_user(
        workspace=workspace, user=user
    )


##########################################################
# get project
##########################################################


async def get_project(project_id: UUID, get_workspace=False) -> Project:
    return await projects_repositories.get_project(
        project_id=project_id,
        select_related=["workspace"] if get_workspace else [None],
    )


async def get_project_detail(
    project: Project, user: AnyUser
) -> ProjectDetailSerializer:
    if (
        user.project_role is not None
        and ProjectPermissions.VIEW_WORKFLOW in user.project_role.permissions
    ):
        workflows = [
            w
            async for w in workflows_repositories.list_workflows_qs(
                filters={
                    "project_id": project.id,
                }
            ).values("id", "name", "slug", "project_id")
        ]
    else:
        workflows = []

    return ProjectDetailSerializer(
        id=project.id,
        name=project.name,
        slug=project.slug,
        description=project.description,
        color=project.color,
        logo=project.logo,
        landing_page=project.landing_page,
        workspace_id=project.workspace_id,
        modified_at=project.modified_at,
        workflows=workflows,
        user_role=user.project_role,
        user_is_invited=user.is_invited or False,
    )


##########################################################
# update project
##########################################################


async def update_project(
    project: Project, updated_by: User, values: dict[str, Any] = {}
) -> ProjectDetailSerializer:
    updated_project = await _update_project(project=project, values=values)
    project_detail = await get_project_detail(project=updated_project, user=updated_by)
    await projects_events.emit_event_when_project_is_updated(
        project_detail=project_detail, updated_by=updated_by
    )
    return project_detail


async def update_project_landing_page(
    project: Project, updated_by: User, new_slug: str | None = None
) -> Project:
    if new_slug is None:
        new_slug = await projects_repositories.get_first_workflow_slug(project)
    updated_project = await projects_repositories.update_project(
        project,
        values={"landing_page": get_landing_page_for_workflow(new_slug)},
    )
    project_detail = await get_project_detail(project=updated_project, user=updated_by)
    await projects_events.emit_event_when_project_is_updated(
        project_detail=project_detail, updated_by=updated_by
    )
    return updated_project


async def _update_project(project: Project, values: dict[str, Any] = {}) -> Project:
    # Prevent hitting the database with an empty PATCH
    if len(values) == 0:
        return project

    file_to_delete = None
    if "logo" in values:
        if logo := values.get("logo"):
            values["logo"] = logo
        else:
            values["logo"] = None

        # Mark a file to-delete
        if project.logo:
            file_to_delete = project.logo.name

    # Update project
    updated_project = await projects_repositories.update_project(
        project=project, values=values
    )

    # Delete old file if existed
    if file_to_delete:
        await projects_tasks.delete_old_logo.defer_async(file_name=file_to_delete)

    return updated_project


##########################################################
# delete project
##########################################################


@transaction_atomic_async
async def delete_project(project: Project, deleted_by: User) -> bool:
    # Mark the file to delete
    file_to_delete = None
    if project.logo:
        file_to_delete = project.logo.name

    deleted = await projects_repositories.delete_projects(project_id=project.id)

    if deleted > 0:
        # Delete old file if existed
        if file_to_delete:
            await projects_tasks.delete_old_logo.defer_async(file_name=file_to_delete)

        # Emit event
        await transaction_on_commit_async(
            projects_events.emit_event_when_project_is_deleted
        )(
            workspace_id=project.workspace_id,
            project=project,
            deleted_by=deleted_by,
        )

        return True

    return False


##########################################################
# misc
##########################################################


async def get_logo(
    project: Project, format: ImageSizeFormat
) -> FieldFile | ThumbnailFile | None:
    match format:
        case "small":
            return await get_thumbnail(
                project.logo, settings.IMAGES.THUMBNAIL_FORMAT_SMALL
            )
        case "large":
            return await get_thumbnail(
                project.logo, settings.IMAGES.THUMBNAIL_FORMAT_LARGE
            )
        case "original":
            return project.logo


async def get_logo_url(project: Project, format: ImageSizeFormat) -> str | None:
    if project.logo:
        thumbnail = await get_logo(project, format)
        if thumbnail:
            return get_absolute_url(thumbnail.url)
    return None
