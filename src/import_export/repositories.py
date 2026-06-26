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

from django.core.files import File

from commons.utils import transaction_atomic_async, transaction_on_commit_async
from import_export.models import (
    ImportationStatus,
    ProjectImportation,
    ProjectImportationType,
)
from ninja_jwt.utils import aware_utcnow
from users.models import User
from workspaces.workspaces.models import Workspace

##########################################################
# create project importation
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
#  get project importation
##########################################################


async def get_project_importation(project_importation_id: UUID) -> ProjectImportation:
    qs = ProjectImportation.objects.all()
    qs = qs.select_related("created_by", "workspace", "project")
    return await qs.aget(id=project_importation_id)


##########################################################
# update project importation
##########################################################


async def update_project_importation(
    project_importation: ProjectImportation, values: dict[str, Any] = {}
) -> ProjectImportation:
    for attr, value in values.items():
        setattr(project_importation, attr, value)

    project_importation.modified_at = aware_utcnow()
    await project_importation.asave(update_fields={*values.keys(), "modified_at"})
    return project_importation


##########################################################
# list project importations
##########################################################


async def list_workspace_project_importations_for_user(
    workspace: Workspace, user: User
) -> list[ProjectImportation]:
    qs = (
        ProjectImportation.objects.filter(
            created_by=user,
            workspace=workspace,
        )
        .select_related("project")
        .exclude(status=ImportationStatus.SUCCESS)
        .distinct()
        .order_by("-created_at")
    )

    return [pi async for pi in qs]


##########################################################
# delete project importations
########################################################


@transaction_atomic_async
async def delete_project_importation(project_importation: ProjectImportation) -> int:
    # don't call project_importation.adelete directly since it will set id to None and we might need it for events
    count, _ = await ProjectImportation.objects.filter(
        id=project_importation.id
    ).adelete()
    await transaction_on_commit_async(project_importation.source.delete)(save=False)
    return count
