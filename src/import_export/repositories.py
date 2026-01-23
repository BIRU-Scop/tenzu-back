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

from import_export.models import Importation, ImportationType
from users.models import User
from workspaces.workspaces.models import Workspace

##########################################################
# create importation
##########################################################


async def create_importation(
    user: User,
    workspace: Workspace,
    origin_type: ImportationType,
    source_file: File,
) -> Importation:
    importation = Importation(
        created_by=user,
        origin_type=origin_type,
        source=source_file,
        extra_data={"workspace_id": workspace.b64id},
    )

    await importation.asave()

    return importation


##########################################################
#  get importation
##########################################################


async def get_importation(importation_id: UUID) -> Importation:
    qs = Importation.objects.all()
    return await qs.aget(id=importation_id)
