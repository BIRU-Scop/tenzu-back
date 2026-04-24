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
from ninja.errors import ValidationError

from import_export import repositories as import_export_repositories
from import_export.models import (
    ImportationStatus,
    ProjectImportation,
    ProjectImportationType,
)
from import_export.serializers import (
    ProjectImportationDetailSerializer,
    TaigaProjectImport,
)
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
) -> ProjectImportationDetailSerializer:
    try:
        importation = await import_export_repositories.create_project_importation(
            user=user,
            workspace=workspace,
            origin_type=origin_type,
            source_file=source,
        )
    except SuspiciousFileOperation as e:
        msg = gettext("Suspicious file, try to shorten the file name")
        raise ValidationError(
            [
                {
                    "type": "value_error",
                    "loc": ["file", "source"],
                    "msg": f"Value error, {msg}",
                    "ctx": {"error": msg},
                }
            ]
        ) from e

    match origin_type:
        case ProjectImportationType.TAIGA:
            await import_taiga_project.defer_async(
                project_importation_id=importation.b64id,
            )
        case _:
            raise NotImplementedError
    return ProjectImportationDetailSerializer.from_orm(importation)


async def do_import_taiga_project(project_importation: ProjectImportation):
    with project_importation.source.open() as source_file:
        taiga_project = TaigaProjectImport.model_validate_json(source_file.read())

    # TODO use a minimal serializer instead, without unused fields, for more efficient parsing
    if taiga_project.__pydantic_extra__:
        logger.warning(f"Import contains extra data: {taiga_project.__pydantic_extra_}")

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
    await update_project_importation(
        project_importation, {"status": ImportationStatus.ONGOING, "project": project}
    )


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
) -> ProjectImportationDetailSerializer:
    updated_project_importation = (
        await import_export_repositories.update_project_importation(
            project_importation=project_importation, values=values
        )
    )
    project_detail = ProjectImportationDetailSerializer(
        status=updated_project_importation.status,
        origin_type=updated_project_importation.origin_type,
    )
    # TODO send event about progress
    # await projects_events.emit_event_when_project_is_updated(
    #     project_detail=project_detail, updated_by=updated_by
    # )
    return project_detail
