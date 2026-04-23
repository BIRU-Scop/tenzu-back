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
from uuid import UUID

from django.core.exceptions import SuspiciousFileOperation
from django.utils.translation import gettext
from ninja import UploadedFile
from ninja.errors import ValidationError

from import_export import repositories as import_export_repositories
from import_export.models import ProjectImportation, ProjectImportationType
from import_export.serializers import ProjectImportationDetailSerializer
from import_export.tasks import import_taiga_project
from users.models import User
from workspaces.workspaces.models import Workspace

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


##########################################################
# get importation
##########################################################


async def get_project_importation(
    project_importation_id: UUID,
) -> ProjectImportation | None:
    return await import_export_repositories.get_project_importation(
        project_importation_id=project_importation_id
    )
