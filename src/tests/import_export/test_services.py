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
import uuid
from pathlib import Path
from unittest.mock import patch

import pytest
from django.core.exceptions import SuspiciousFileOperation
from django.core.files.uploadedfile import UploadedFile
from ninja.errors import ValidationError

from import_export import services
from import_export.models import (
    ImportationStatus,
    ProjectImportation,
    ProjectImportationType,
)
from import_export.serializers import ProjectImportationSerializer
from projects.projects.models import Project
from tests.utils import factories as f
from tests.utils.taskqueue import TestTasksQueueManager

##########################################################
# import_project
##########################################################


async def test_import_project(tqmanager):
    importation = f.build_project_importation()

    with (
        patch(
            "import_export.services.import_export_repositories", autospec=True
        ) as fake_import_export_repositories,
    ):
        fake_import_export_repositories.create_project_importation.return_value = (
            importation
        )
        serialised_importation = await services.import_project(
            user=importation.created_by,
            workspace=importation.workspace,
            origin_type=importation.origin_type,
            source=importation.source,
        )

        assert isinstance(serialised_importation, ProjectImportationSerializer)
        assert len(tqmanager.pending_jobs) == 1


@pytest.mark.django_db
async def test_do_import_project_no_kanban(tqmanager: TestTasksQueueManager, caplog):
    workspace = await f.create_workspace()
    source_path = Path(__file__).resolve().parent / "samples" / "no-kanban.json"
    with open(source_path) as source_file:
        await services.import_project(
            user=workspace.created_by,
            workspace=workspace,
            origin_type=ProjectImportationType.TAIGA,
            source=UploadedFile(source_file),
        )
    assert len(tqmanager.pending_jobs) == 1
    await tqmanager.run_async()
    project = await Project.objects.aget()
    importation = await ProjectImportation.objects.select_related("project").aget()
    assert project.created_at.year == 2025
    assert importation.status == ImportationStatus.SUCCESS
    assert importation.project == project
    assert not caplog.records


@pytest.mark.django_db
async def test_do_import_project_complete(tqmanager: TestTasksQueueManager, caplog):
    workspace = await f.create_workspace()
    source_path = (
        Path(__file__).resolve().parent
        / "samples"
        / "export_from_taiga_project1_small.json"
    )
    with open(source_path) as source_file:
        await services.import_project(
            user=workspace.created_by,
            workspace=workspace,
            origin_type=ProjectImportationType.TAIGA,
            source=UploadedFile(source_file),
        )
    assert len(tqmanager.pending_jobs) == 1
    await tqmanager.run_async()
    project = await Project.objects.aget()
    importation = await ProjectImportation.objects.select_related("project").aget()
    assert project.created_at.year == 2025
    assert importation.status == ImportationStatus.ONGOING
    assert importation.project == project
    assert not caplog.records


async def test_import_project_suspicious_file():
    importation = f.build_project_importation()

    with (
        patch(
            "import_export.services.import_export_repositories", autospec=True
        ) as fake_import_export_repositories,
    ):
        fake_import_export_repositories.create_project_importation.side_effect = (
            SuspiciousFileOperation()
        )
        with pytest.raises(ValidationError):
            await services.import_project(
                user=importation.created_by,
                workspace=importation.workspace,
                origin_type=importation.origin_type,
                source=importation.source,
            )


async def test_import_project_not_supported():
    importation = f.build_project_importation(origin_type=ProjectImportationType.TRELLO)

    with (
        patch(
            "import_export.services.import_export_repositories", autospec=True
        ) as fake_import_export_repositories,
    ):
        fake_import_export_repositories.create_project_importation.return_value = (
            importation
        )
        with pytest.raises(NotImplementedError):
            await services.import_project(
                user=importation.created_by,
                workspace=importation.workspace,
                origin_type=importation.origin_type,
                source=importation.source,
            )


##########################################################
# get_importation
##########################################################


async def test_get_importation():
    with (
        patch(
            "import_export.services.import_export_repositories", autospec=True
        ) as fake_import_export_repositories,
    ):
        await services.get_project_importation(project_importation_id=uuid.uuid1())
        fake_import_export_repositories.get_project_importation.assert_called()


##########################################################
# update_project_importation
##########################################################


async def test_update_project_importation():
    importation = f.build_project_importation()
    with (
        patch(
            "import_export.services.import_export_repositories", autospec=True
        ) as fake_import_export_repositories,
    ):
        await services.update_project_importation(importation, {})
        fake_import_export_repositories.update_project_importation.assert_called()


##########################################################
# list_workspace_project_importations_for_user
##########################################################


async def test_list_workspace_project_importations_for_user():
    workspace = f.build_workspace()
    with (
        patch(
            "import_export.services.import_export_repositories", autospec=True
        ) as fake_import_export_repositories,
    ):
        await services.list_workspace_project_importations_for_user(
            workspace, workspace.created_by
        )
        fake_import_export_repositories.list_workspace_project_importations_for_user.assert_called()
