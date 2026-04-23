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

from django.core.files import File

from import_export.models import ProjectImportation, ProjectImportationType
from users.models import User
from workspaces.workspaces.models import Workspace

##########################################################
# create importation
##########################################################


async def create_project_importation(
    user: User,
    workspace: Workspace,
    origin_type: ProjectImportationType,
    source_file: File,
) -> ProjectImportation:
    importation = ProjectImportation(
        created_by=user,
        origin_type=origin_type,
        source=source_file,
        workspace=workspace,
    )

    await importation.asave()

    return importation


##########################################################
#  get importation
##########################################################


async def get_project_importation(project_importation_id: UUID) -> ProjectImportation:
    qs = ProjectImportation.objects.all()
    return await qs.aget(id=project_importation_id)
