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
from unittest.mock import Mock, patch

import pytest
from django.core.exceptions import SuspiciousFileOperation
from ninja.errors import ValidationError

from import_export import services
from import_export.models import (
    ImportationStatus,
    ProjectImportationType,
)
from import_export.serializers import ProjectImportationSerializer
from import_export.services.exceptions import IncompatibleImportationStatus
from tests.utils import factories as f
from tests.utils.utils import patch_db_transaction

##########################################################
# import_project
##########################################################


async def test_import_project(tqmanager):
    project_importation = f.build_project_importation()

    with (
        patch(
            "import_export.services.import_export_repositories", autospec=True
        ) as fake_import_export_repositories,
        patch(
            "import_export.services.import_export_events", autospec=True
        ) as fake_import_export_events,
        patch_db_transaction(),
    ):
        fake_import_export_repositories.create_project_importation.return_value = (
            project_importation
        )
        serialised_importation = await services.import_project(
            user=project_importation.created_by,
            workspace=project_importation.workspace,
            origin_type=project_importation.origin_type,
            source=project_importation.source,
        )

        fake_import_export_events.emit_event_when_project_importation_is_created.assert_awaited_once_with(
            project_importation=project_importation
        )
        assert isinstance(serialised_importation, ProjectImportationSerializer)
        assert len(tqmanager.pending_jobs) == 1


async def test_import_project_suspicious_file():
    importation = f.build_project_importation()

    with (
        patch(
            "import_export.services.import_export_repositories", autospec=True
        ) as fake_import_export_repositories,
        patch_db_transaction(),
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
        patch_db_transaction(),
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
        patch(
            "import_export.services.import_export_events", autospec=True
        ) as fake_import_export_events,
        patch_db_transaction(),
    ):
        await services.update_project_importation(importation, {})
        fake_import_export_repositories.update_project_importation.assert_called()
        fake_import_export_events.emit_event_when_project_importation_is_updated.assert_called()


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


##########################################################
# delete_project_importation
##########################################################


async def test_delete_project_fail():
    project_importation = f.build_project_importation(status=ImportationStatus.SUCCESS)

    with (
        patch(
            "import_export.services.projects_services", autospec=True
        ) as fake_projects_services,
        patch(
            "import_export.services.import_export_repositories", autospec=True
        ) as fake_import_export_repositories,
        patch(
            "import_export.services.import_export_events", autospec=True
        ) as fake_import_export_events,
        patch_db_transaction(),
        pytest.raises(IncompatibleImportationStatus),
    ):
        await services.delete_project_importation(
            project_importation=project_importation
        )

    fake_projects_services.delete_project.assert_not_awaited()
    fake_import_export_repositories.delete_project_importation.assert_not_awaited()
    fake_import_export_events.emit_event_when_project_importation_is_deleted.assert_not_awaited()


async def test_delete_project_ok():
    with (
        patch(
            "import_export.services.projects_services", autospec=True
        ) as fake_projects_services,
        patch(
            "import_export.services.import_export_repositories", autospec=True
        ) as fake_import_export_repositories,
        patch(
            "import_export.services.import_export_events", autospec=True
        ) as fake_import_export_events,
        patch_db_transaction(),
    ):
        fake_import_export_repositories.delete_project_importation.return_value = 1
        # failure without project
        project_importation = f.build_project_importation(
            status=ImportationStatus.FAILURE, project=None
        )
        await services.delete_project_importation(
            project_importation=project_importation
        )

        fake_import_export_repositories.cancel_project_importation.assert_not_awaited()
        fake_projects_services.delete_project.assert_not_awaited()
        fake_import_export_repositories.delete_project_importation.assert_awaited_once_with(
            project_importation=project_importation
        )
        fake_import_export_events.emit_event_when_project_importation_is_deleted.assert_awaited_once_with(
            workspace_id=project_importation.workspace_id,
            project_importation_id=project_importation.id,
            importation_owner=project_importation.created_by,
        )

        # ongoing with project
        fake_import_export_repositories.delete_project_importation.reset_mock()
        fake_import_export_events.emit_event_when_project_importation_is_deleted.reset_mock()
        project_importation = f.build_project_importation(
            status=ImportationStatus.ONGOING, created_by=project_importation.created_by
        )
        await services.delete_project_importation(
            project_importation=project_importation
        )

        fake_import_export_repositories.cancel_project_importation.assert_awaited_once_with(
            project_importation=project_importation
        )
        fake_projects_services.delete_project.assert_awaited_with(
            project_importation.project, deleted_by=project_importation.created_by
        )
        fake_import_export_repositories.delete_project_importation.assert_awaited_with(
            project_importation=project_importation
        )
        fake_import_export_events.emit_event_when_project_importation_is_deleted.assert_awaited_once_with(
            workspace_id=project_importation.workspace_id,
            project_importation_id=project_importation.id,
            importation_owner=project_importation.created_by,
        )


##########################################################
# handle_project_importation_pending_invites
##########################################################


async def test_handle_project_importation_pending_invites_fail():
    project_importation = f.build_project_importation(status=ImportationStatus.PENDING)

    with (
        patch(
            "projects.invitations.api", autospec=True
        ) as fake_projects_invitations_apis,
        patch(
            "import_export.services.import_export_repositories", autospec=True
        ) as fake_import_export_repositories,
        patch(
            "import_export.services.import_export_events", autospec=True
        ) as fake_import_export_events,
        patch(
            "import_export.services.projects_events", autospec=True
        ) as fake_projects_events,
        patch_db_transaction(),
        pytest.raises(IncompatibleImportationStatus),
    ):
        await services.handle_project_importation_pending_invites(
            project_importation, Mock(), Mock()
        )

    fake_projects_invitations_apis.create_project_invitations.assert_not_awaited()
    fake_import_export_repositories.update_project_importation.assert_not_awaited()
    fake_import_export_events.emit_event_when_project_importation_is_updated.assert_not_awaited()
    fake_projects_events.emit_event_when_project_is_created.assert_not_awaited()
