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
from pathlib import Path

from import_export.models import ProjectImportation
from import_export.notifications.content import (
    ProjectImportationFailNotificationContent,
    ProjectImportationWarningFileNotificationContent,
)
from notifications import services as notifications_services

PROJECT_IMPORTATION_FAILURE = "project_importation.fail"
PROJECT_IMPORTATION_WARNING_FILE_TOO_BIG = "project_importation.warning.file_too_big"


async def notify_when_project_importation_fail(
    project_importation: ProjectImportation,
) -> None:
    await notifications_services.notify_users(
        notification_type=PROJECT_IMPORTATION_FAILURE,
        emitted_by=None,
        notified_user_ids=[project_importation.created_by_id],
        content=ProjectImportationFailNotificationContent(
            workspace=project_importation.workspace,
            project_importation=project_importation,
        ),
    )


async def notify_when_project_importation_file_too_big_warning(
    project_importation: ProjectImportation, file_name: str, file_size: int
) -> None:
    await notifications_services.notify_users(
        notification_type=PROJECT_IMPORTATION_WARNING_FILE_TOO_BIG,
        emitted_by=None,
        notified_user_ids=[project_importation.created_by_id],
        content=ProjectImportationWarningFileNotificationContent(
            project=project_importation.project,
            project_importation=project_importation,
            file_name=file_name,
            file_size=file_size,
        ),
    )
