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
from uuid import UUID

from ninja import File, Form, Path, Router, Status

from base.serializers import BaseDataSchema
from commons.exceptions import api as ex
from commons.exceptions.api.errors import (
    ERROR_RESPONSE_400,
    ERROR_RESPONSE_403,
    ERROR_RESPONSE_404,
    ERROR_RESPONSE_422,
)
from commons.validators import B64UUID
from import_export import services as import_export_services
from import_export.api.validators import ImportationFileField, ImportProjectValidator
from import_export.models import ProjectImportation
from import_export.permissions import ProjectImportationPermissionsCheck
from import_export.serializers import (
    InvitedProjectImportationSerializer,
    ProjectImportationSerializer,
)
from memberships.api.validators import InvitationsValidator
from permissions import (
    check_permissions,
)
from workspaces.workspaces.api import get_workspace_or_404

import_export_router = Router()


##########################################################
# create importation
##########################################################


@import_export_router.post(
    "/workspaces/{workspace_id}/projects/importations",
    url_name="importation.projects.create",
    summary="Create and launch a project importation",
    response={
        200: BaseDataSchema[ProjectImportationSerializer],
        400: ERROR_RESPONSE_400,
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    tags=["workspaces", "projects", "import_export"],
    by_alias=True,
)
async def launch_project_importation(
    request,
    workspace_id: Path[B64UUID],
    form: Form[ImportProjectValidator],
    source: File[ImportationFileField],
) -> ProjectImportationSerializer:
    """
    Launch an importation for a project in a given workspace.
    """
    workspace = await get_workspace_or_404(workspace_id=workspace_id)

    await check_permissions(
        permissions=ProjectImportationPermissionsCheck.CREATE.value,
        user=request.user,
        obj=workspace,
    )
    return await import_export_services.import_project(
        user=request.user,
        workspace=workspace,
        origin_type=form.origin_type,
        source=source,
    )


##########################################################
# list project importations
##########################################################


@import_export_router.get(
    "/workspaces/{workspace_id}/projects/importations",
    url_name="importation.projects.list",
    summary="List workspace project importations",
    response={
        200: BaseDataSchema[list[ProjectImportationSerializer]],
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    tags=["workspaces", "projects", "import_export"],
    by_alias=True,
)
async def list_project_importations(
    request, workspace_id: Path[B64UUID]
) -> list[ProjectImportation]:
    """
    List project importations for a workspace launched by the user.
    """
    workspace = await get_workspace_or_404(workspace_id=workspace_id)
    await check_permissions(
        permissions=ProjectImportationPermissionsCheck.VIEW.value,
        user=request.user,
        obj=workspace,
    )
    return await import_export_services.list_workspace_project_importations_for_user(
        workspace=workspace, user=request.user
    )


##########################################################
# delete project
##########################################################


@import_export_router.delete(
    "/projects/importations/{project_importation_id}",
    url_name="importations.projects.delete",
    summary="Delete project importation",
    response={
        204: None,
        400: ERROR_RESPONSE_400,
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def delete_project_importation(
    request,
    project_importation_id: Path[B64UUID],
) -> Status[None]:
    """
    Delete a project importation
    """
    project_importation = await get_project_importation_or_404(project_importation_id)
    await check_permissions(
        permissions=ProjectImportationPermissionsCheck.DELETE.value,
        user=request.user,
        obj=project_importation,
    )

    await import_export_services.delete_project_importation(
        project_importation=project_importation
    )
    return Status(204, None)


##########################################################
# actions
##########################################################


@import_export_router.post(
    "/projects/importations/{project_importation_id}/invite",
    url_name="importations.projects.invite",
    summary="Handle the project importation pending invites",
    response={
        200: InvitedProjectImportationSerializer,
        400: ERROR_RESPONSE_400,
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def handle_project_importation_pending_invites(
    request,
    project_importation_id: Path[B64UUID],
    form: InvitationsValidator,
) -> InvitedProjectImportationSerializer:
    """
    Handle the pending invites of an importation and remove the action_needed flag from it.
    Invitation list can be filled or empty (ignore action)
    """
    project_importation = await get_project_importation_or_404(project_importation_id)
    await check_permissions(
        permissions=ProjectImportationPermissionsCheck.ACT.value,
        user=request.user,
        obj=project_importation,
    )
    return await import_export_services.handle_project_importation_pending_invites(
        project_importation=project_importation, invitations_form=form, request=request
    )


##########################################################
# misc get project importation or 404
##########################################################


async def get_project_importation_or_404(
    project_importation_id: UUID,
) -> ProjectImportation:
    try:
        project_importation = await import_export_services.get_project_importation(
            project_importation_id=project_importation_id
        )
    except ProjectImportation.DoesNotExist as e:
        raise ex.NotFoundError("Project Importation does not exist") from e

    return project_importation
