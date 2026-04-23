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
from ninja import File, Form, Path, Router

from base.serializers import BaseDataModel
from commons.exceptions.api.errors import (
    ERROR_RESPONSE_400,
    ERROR_RESPONSE_403,
    ERROR_RESPONSE_404,
    ERROR_RESPONSE_422,
)
from commons.validators import B64UUID
from import_export import services as import_export_services
from import_export.api.validators import ImportationFileField, ImportProjectValidator
from import_export.serializers import ProjectImportationDetailSerializer
from permissions import (
    check_permissions,
)
from projects.projects.permissions import ProjectPermissionsCheck
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
        200: BaseDataModel[ProjectImportationDetailSerializer],
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
) -> ProjectImportationDetailSerializer:
    """
    Launch an importation for a project in a given workspace.
    """
    workspace = await get_workspace_or_404(workspace_id=workspace_id)

    await check_permissions(
        permissions=ProjectPermissionsCheck.CREATE.value,
        user=request.user,
        obj=workspace,
    )
    return await import_export_services.import_project(
        user=request.user,
        workspace=workspace,
        origin_type=form.origin_type,
        source=source,
    )
