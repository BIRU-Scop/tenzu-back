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
import logging
from typing import Any
from uuid import UUID

from django.core.exceptions import SuspiciousFileOperation
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils.translation import gettext
from ninja import UploadedFile
from ninja.errors import ValidationError as APIValidationError
from pydantic import ValidationError
from pydantic_core import ErrorDetails

from import_export import notifications
from import_export import repositories as import_export_repositories
from import_export.models import (
    ImportationError,
    ImportationStatus,
    ProjectImportation,
    ProjectImportationType,
)
from import_export.serializers import (
    ProjectImportationSerializer,
    TaigaProjectImport,
)
from import_export.serializers.taiga import FullTaigaProjectImport
from import_export.tasks import import_taiga_project
from projects.projects import services as projects_services
from users.models import User
from workspaces.workspaces.models import Workspace

logger = logging.getLogger(__name__)


##########################################################
# import project
##########################################################


async def import_project(
    user: User,
    workspace: Workspace,
    origin_type: ProjectImportationType,
    source: UploadedFile,
) -> ProjectImportationSerializer:
    try:
        importation = await import_export_repositories.create_project_importation(
            user=user,
            workspace=workspace,
            origin_type=origin_type,
            source_file=source,
        )
    except SuspiciousFileOperation as e:
        msg = gettext("Suspicious file, try to shorten the file name")
        raise APIValidationError(
            [
                ErrorDetails(
                    type="suspicious_file_operation",
                    loc=["file", "source"],
                    msg=msg,
                    ctx={"error": msg},
                    input=source.name,
                )
            ]
        ) from e

    match origin_type:
        case ProjectImportationType.TAIGA:
            await import_taiga_project.defer_async(
                project_importation_id=importation.b64id,
            )
        case _:
            raise NotImplementedError
    return ProjectImportationSerializer.from_orm(importation)


async def do_import_taiga_project(project_importation: ProjectImportation):
    with project_importation.source.open() as source_file:
        try:
            taiga_project = TaigaProjectImport.model_validate_json(source_file.read())
        except ValidationError as e:
            await update_project_importation(
                project_importation,
                {
                    "status": ImportationStatus.FAILURE,
                    "extra_data": {"error_code": ImportationError.INVALID},
                },
            )
            await notifications.notify_when_project_importation_fail(
                project_importation
            )
            logger.warning(
                f"Project import {project_importation.id} validation failed: {e}"
            )
            return

    extra_fields = FullTaigaProjectImport.filter_unknown_fields(
        taiga_project.__pydantic_extra__
    )
    if extra_fields:
        logger.warning(
            f"Project import {project_importation.id} contains extra data: {extra_fields}"
        )

    # TODO add transaction and rollback if later error
    project = await projects_services._create_project(
        workspace=project_importation.workspace,
        name=taiga_project.name,
        description=taiga_project.description,
        created_by=project_importation.created_by,
        color=None,
        logo_file=SimpleUploadedFile(taiga_project.logo.name, taiga_project.logo.data)
        if taiga_project.logo is not None
        else None,
    )
    await projects_services._update_project(
        project, {"created_at": taiga_project.created_date}
    )
    await update_project_importation(
        project_importation, {"status": ImportationStatus.ONGOING, "project": project}
    )
    # TODO users

    if not taiga_project.is_kanban_activated:
        await update_project_importation(
            project_importation,
            {"status": ImportationStatus.SUCCESS},
        )
        return
    # TODO stories


##########################################################
# get importation
##########################################################


async def get_project_importation(
    project_importation_id: UUID,
) -> ProjectImportation | None:
    return await import_export_repositories.get_project_importation(
        project_importation_id=project_importation_id
    )


##########################################################
# update importation
##########################################################


async def update_project_importation(
    project_importation: ProjectImportation, values: dict[str, Any] = {}
) -> ProjectImportation:
    updated_project_importation = (
        await import_export_repositories.update_project_importation(
            project_importation=project_importation, values=values
        )
    )
    # TODO send event about progress or error, send project creation event on success
    # await projects_events.emit_event_when_project_is_updated(
    #     project_detail=project_detail, updated_by=updated_by
    # )
    return updated_project_importation


##########################################################
# list projects
##########################################################


async def list_workspace_project_importations_for_user(
    workspace: Workspace, user: User
) -> list[ProjectImportation]:
    return (
        await import_export_repositories.list_workspace_project_importations_for_user(
            workspace=workspace, user=user
        )
    )
