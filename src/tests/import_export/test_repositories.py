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
from uuid import uuid1

import pytest

from base.db.models.mixins import CreatedByMetaInfoMixin
from import_export import repositories
from import_export.models import (
    ImportationStatus,
    ProjectImportation,
    ProjectImportationType,
)
from tests.utils import factories as f
from tests.utils.bad_params import NOT_EXISTING_UUID

pytestmark = pytest.mark.django_db


##########################################################
# create_importation
##########################################################


async def test_create_importation():
    source_file = f.build_string_file()
    workspace = await f.create_workspace()
    user = await f.create_user()
    importation = await repositories.create_project_importation(
        user=user,
        workspace=workspace,
        origin_type=ProjectImportationType.TAIGA,
        source_file=source_file,
    )
    assert importation.source.name.endswith(source_file.name)
    assert importation.created_by_id == user.id
    assert importation.workspace_id == workspace.id
    assert importation.extra_data == {}
    return importation


##########################################################
# get_importation
##########################################################


async def test_get_importation_return_importation():
    importation = await f.create_project_importation(project=None)
    assert (
        await repositories.get_project_importation(
            project_importation_id=importation.id
        )
        == importation
    )


async def test_get_importation_not_exists():
    with pytest.raises(ProjectImportation.DoesNotExist):
        await repositories.get_project_importation(
            project_importation_id=NOT_EXISTING_UUID
        )


##########################################################
# update_project_importation
##########################################################


async def test_update_project_importation():
    importation = await f.create_project_importation(project=None)
    assert importation.modified_at is None
    importation = await repositories.update_project_importation(
        importation, {"status": ImportationStatus.SUCCESS}
    )
    assert importation.modified_at is not None
    assert importation.status == ImportationStatus.SUCCESS


##########################################################
# list_workspace_project_importations_for_user
##########################################################


async def test_list_workspace_project_importations_for_user() -> (
    list[ProjectImportation]
):
    workspace = await f.create_workspace()
    await f.create_project_importation(
        created_by=workspace.created_by, workspace=workspace, project=None
    )
    await f.create_project_importation(
        created_by=workspace.created_by,
        workspace=workspace,
        project=None,
        status=ImportationStatus.ONGOING,
    )
    await f.create_project_importation(
        created_by=workspace.created_by,
        workspace=workspace,
        project=None,
        status=ImportationStatus.PENDING,
    )
    await f.create_project_importation(
        created_by=workspace.created_by,
        workspace=workspace,
        project=None,
        status=ImportationStatus.ACTION_NEEDED,
    )
    await f.create_project_importation(
        created_by=workspace.created_by,
        workspace=workspace,
        project=None,
        status=ImportationStatus.FAILURE,
    )

    # excluded
    await f.create_project_importation(
        created_by=workspace.created_by,
        workspace=workspace,
        project=None,
        status=ImportationStatus.SUCCESS,
    )  # because success
    await f.create_project_importation(
        created_by=workspace.created_by, project=None
    )  # because other workspace
    other_user = await f.create_user()
    await f.create_project_importation(
        created_by=other_user, workspace=workspace, project=None
    )  # because other user
    assert (
        len(
            await repositories.list_workspace_project_importations_for_user(
                workspace, workspace.created_by
            )
        )
        == 5
    )
