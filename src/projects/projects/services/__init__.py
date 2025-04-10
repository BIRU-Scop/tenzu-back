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

from functools import partial
from typing import Any
from uuid import UUID

from asgiref.sync import sync_to_async
from django.conf import settings
from ninja import UploadedFile

from base.utils.files import uploadfile_to_file
from base.utils.images import get_thumbnail_url
from commons.utils import transaction_atomic_async
from events import event_handlers as actions_events
from permissions import services as permissions_services
from projects.invitations import services as pj_invitations_services
from projects.invitations.choices import ProjectInvitationStatus
from projects.memberships import repositories as pj_memberships_repositories
from projects.projects import events as projects_events
from projects.projects import repositories as projects_repositories
from projects.projects import tasks as projects_tasks
from projects.projects.models import Project
from projects.projects.serializers import ProjectDetailSerializer
from projects.projects.serializers import services as serializers_services
from projects.projects.services import exceptions as ex
from projects.roles import repositories as pj_roles_repositories
from users import services as users_services
from users.models import AnyUser, User
from workflows import repositories as workflows_repositories
from workspaces.memberships import repositories as workspace_memberships_repositories
from workspaces.workspaces import services as workspaces_services
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
    template = await projects_repositories.get_project_template(
        filters={"slug": settings.DEFAULT_PROJECT_TEMPLATE}
    )

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

    # apply template
    if template:
        await projects_repositories.apply_template_to_project(
            template=template, project=project
        )
    else:
        raise Exception(
            f"Default project template '{settings.DEFAULT_PROJECT_TEMPLATE}' not found. "
            "Try to load fixtures again and check if the error persist."
        )

    # assign 'created_by' to the project as 'admin' role
    if admin_role := await pj_roles_repositories.get_project_role(
        filters={"project_id": project.id, "slug": "admin"}
    ):
        await pj_memberships_repositories.create_project_membership(
            user=created_by, project=project, role=admin_role
        )
    else:
        raise Exception(
            "Default project template does not have a role with the slug 'admin'. "
            "Try to load fixtures again and check if the error persist."
        )

    return project


##########################################################
# list projects
##########################################################


async def list_projects(workspace_id: UUID) -> list[Project]:
    return await projects_repositories.list_projects(
        filters={"workspace_id": workspace_id},
        select_related=["workspace"],
    )


async def list_workspace_projects_for_user(
    workspace: Workspace, user: User
) -> list[Project]:
    ws_membership = await workspace_memberships_repositories.get_workspace_membership(
        filters={"workspace_id": workspace.id, "user_id": user.id},
        select_related=[],
    )
    if ws_membership:
        return await list_projects(workspace_id=workspace.id)

    return await projects_repositories.list_projects(
        filters={"workspace_id": workspace.id, "memberships__user_id": user.id},
        select_related=["workspace"],
    )


async def list_workspace_invited_projects_for_user(
    workspace: Workspace, user: User
) -> list[Project]:
    return await projects_repositories.list_projects(
        filters={
            "workspace_id": workspace.id,
            "invitations__user_id": user.id,
            "invitations__status": ProjectInvitationStatus.PENDING,
        }
    )


##########################################################
# get project
##########################################################


async def get_project(id: UUID) -> Project | None:
    return await projects_repositories.get_project(
        project_id=id, select_related=["workspace"], prefetch_related=["workflows"]
    )


async def get_project_detail(
    project: Project, user: AnyUser
) -> ProjectDetailSerializer:
    (
        is_project_admin,
        is_project_member,
        project_role_permissions,
    ) = await permissions_services.get_user_project_role_info(
        user=user, project=project
    )

    is_workspace_member = await permissions_services.is_workspace_member(
        user=user, obj=project.workspace
    )

    user_id = None if user.is_anonymous else user.id
    workspace = await workspaces_services.get_workspace_nested(
        workspace_id=project.workspace_id, user_id=user_id
    )

    user_permissions = await permissions_services.get_user_permissions_for_project(
        is_project_admin=is_project_admin,
        is_project_member=is_project_member,
        is_workspace_member=is_workspace_member,
        is_authenticated=user.is_authenticated,
        project_role_permissions=project_role_permissions,
        project=project,
    )

    user_has_pending_invitation = (
        False
        if user.is_anonymous
        else await pj_invitations_services.has_pending_project_invitation(
            user=user, project=project
        )
    )

    workflows = await workflows_repositories.list_workflows(
        filters={
            "project_id": project.id,
        }
    )

    return serializers_services.serialize_project_detail(
        project=project,
        workspace=workspace,
        workflows=workflows,
        user_is_admin=is_project_admin,
        user_is_member=is_project_member,
        user_permissions=user_permissions,
        user_has_pending_invitation=user_has_pending_invitation,
    )


##########################################################
# update project
##########################################################


async def update_project(
    project: Project, updated_by: User, values: dict[str, Any] = {}
) -> ProjectDetailSerializer:
    updated_project = await _update_project(project=project, values=values)
    project_detail = await get_project_detail(project=updated_project, user=updated_by)
    project_id = updated_project.b64id
    await projects_events.emit_event_when_project_is_updated(
        project_detail=project_detail, project_id=project_id, updated_by=updated_by
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
    project_id = updated_project.b64id
    project_detail = await get_project_detail(project=updated_project, user=updated_by)
    await projects_events.emit_event_when_project_is_updated(
        project_detail=project_detail, project_id=project_id, updated_by=updated_by
    )
    return updated_project


async def _update_project(project: Project, values: dict[str, Any] = {}) -> Project:
    # Prevent hitting the database with an empty PATCH
    if len(values) == 0:
        return project

    if "name" in values:
        if values.get("name") is None or values.get("name") == "":
            raise ex.TenzuValidationError("Name cannot be empty")

    if "description" in values:
        values["description"] = values["description"] or ""

    file_to_delete = None
    if "logo" in values:
        if logo := values.get("logo"):
            values["logo"] = uploadfile_to_file(file=logo)
        else:
            values["logo"] = None

        # Mark a file to-delete
        if project.logo:
            file_to_delete = project.logo.path

    # Update project
    updated_project = await projects_repositories.update_project(
        project=project, values=values
    )

    # Delete old file if existed
    if file_to_delete:
        await sync_to_async(projects_tasks.delete_old_logo.defer)(path=file_to_delete)

    return updated_project


async def update_project_public_permissions(
    project: Project, permissions: list[str]
) -> list[str]:
    await projects_repositories.update_project(
        project=project, values={"public_permissions": permissions}
    )

    # TODO: emit an event to users/project with the new permissions when a change happens?
    await projects_events.emit_event_when_project_permissions_are_updated(
        project=project
    )
    if not permissions:
        await actions_events.emit_event_action_to_check_project_subscription(
            project_b64id=project.b64id
        )

    return permissions


##########################################################
# delete project
##########################################################


async def delete_project(project: Project, deleted_by: User) -> bool:
    # Mark the file to delete
    file_to_delete = None
    if project.logo:
        file_to_delete = project.logo.path

    guests = await users_services.list_guests_in_workspace_for_project(project=project)
    deleted = await projects_repositories.delete_projects(project_id=project.id)

    if deleted > 0:
        # Delete old file if existed
        if file_to_delete:
            await sync_to_async(projects_tasks.delete_old_logo.defer)(
                path=file_to_delete
            )

        # Emit event
        await projects_events.emit_event_when_project_is_deleted(
            workspace=project.workspace,
            project=project,
            deleted_by=deleted_by,
            guests=guests,
        )

        return True

    return False


##########################################################
# misc
##########################################################


async def get_logo_thumbnail_url(
    thumbnailer_size: str, logo_relative_path: str
) -> str | None:
    if logo_relative_path:
        return await get_thumbnail_url(logo_relative_path, thumbnailer_size)
    return None


get_logo_small_thumbnail_url = partial(
    get_logo_thumbnail_url, settings.IMAGES.THUMBNAIL_PROJECT_LOGO_SMALL
)
get_logo_large_thumbnail_url = partial(
    get_logo_thumbnail_url, settings.IMAGES.THUMBNAIL_PROJECT_LOGO_LARGE
)
