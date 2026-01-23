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

from ninja import UploadedFile

from import_export import repositories as import_export_repositories
from import_export.models import Importation, ImportationType
from import_export.serializers import ImportationDetailSerializer
from import_export.tasks import import_taiga_project
from users.models import User
from workspaces.workspaces.models import Workspace

##########################################################
# import project
##########################################################


async def import_project(
    user: User, workspace: Workspace, origin_type: ImportationType, source: UploadedFile
) -> ImportationDetailSerializer:
    importation = await import_export_repositories.create_importation(
        user=user,
        workspace=workspace,
        origin_type=origin_type,
        source_file=source,
    )

    match origin_type:
        case ImportationType.TAIGA:
            await import_taiga_project.defer_async(
                importation_id=importation.id,
            )
    return ImportationDetailSerializer.from_orm(importation)


##########################################################
# get importation
##########################################################


async def get_importation(importation_id: UUID) -> Importation | None:
    return await import_export_repositories.get_importation(
        importation_id=importation_id
    )
