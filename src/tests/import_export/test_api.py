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

import pytest

from import_export.models import (
    ImportationStatus,
    ProjectImportation,
    ProjectImportationType,
)
from projects.projects.models import Project
from tests.utils import factories as f
from tests.utils.bad_params import INVALID_B64ID, NOT_EXISTING_B64ID

pytestmark = pytest.mark.django_db


##########################################################
# POST /workspaces/<id>/projects/importation
##########################################################


async def test_launch_importation_200_ok_being_workspace_member(client):
    workspace = await f.create_workspace()
    data = {
        "originType": ProjectImportationType.TAIGA,
    }
    source = f.build_string_uploadfile(
        "taiga_export", "json", "application/json", content="{}"
    )

    client.login(workspace.created_by)
    response = await client.post(
        f"/workspaces/{workspace.b64id}/projects/importations",
        data=data,
        FILES={"source": source},
    )
    assert response.status_code == 200, response.data["data"]
    res = response.data["data"]
    assert res["status"] == ImportationStatus.PENDING
    importation = await ProjectImportation.objects.aget()
    assert importation.workspace_id == workspace.id


async def test_launch_importation_404_not_found_workspace_error(client):
    workspace = await f.create_workspace()
    data = {
        "originType": ProjectImportationType.TAIGA,
    }
    source = f.build_string_uploadfile(
        "taiga_export", "json", "application/json", content="{}"
    )

    client.login(workspace.created_by)
    response = await client.post(
        f"/workspaces/{NOT_EXISTING_B64ID}/projects/importations",
        data=data,
        FILES={"source": source},
    )
    assert response.status_code == 404, response.data


async def test_launch_importation_403_being_no_workspace_member(client):
    workspace = await f.create_workspace()
    user2 = await f.create_user()
    data = {
        "originType": ProjectImportationType.TAIGA,
    }
    source = f.build_string_uploadfile(
        "taiga_export", "json", "application/json", content="{}"
    )

    client.login(user2)
    response = await client.post(
        f"/workspaces/{workspace.b64id}/projects/importations",
        data=data,
        FILES={"source": source},
    )
    assert response.status_code == 403, response.data


async def test_launch_importation_401_being_anonymous(client):
    workspace = await f.create_workspace()
    data = {
        "originType": ProjectImportationType.TAIGA,
    }
    source = f.build_string_uploadfile(
        "taiga_export", "json", "application/json", content="{}"
    )

    response = await client.post(
        f"/workspaces/{workspace.b64id}/projects/importations",
        data=data,
        FILES={"source": source},
    )
    assert response.status_code == 401, response.data


async def test_launch_importation_422_unprocessable_file(client):
    workspace = await f.create_workspace()
    data = {
        "originType": ProjectImportationType.TAIGA,
    }
    source = f.build_string_uploadfile("taiga_export", "png", "image/png")

    client.login(workspace.created_by)
    response = await client.post(
        f"/workspaces/{workspace.b64id}/projects/importations",
        data=data,
        FILES={"source": source},
    )
    assert response.status_code == 422, response.data


async def test_launch_importation_422_unprocessable_uuid(client):
    workspace = await f.create_workspace()
    data = {
        "originType": ProjectImportationType.TAIGA,
    }
    source = f.build_string_uploadfile(
        "taiga_export", "json", "application/json", content="{}"
    )

    client.login(workspace.created_by)
    response = await client.post(
        f"/workspaces/{INVALID_B64ID}/projects/importations",
        data=data,
        FILES={"source": source},
    )
    assert response.status_code == 422, response.data


##########################################################
# GET /workspaces/<id>/projects/importations
##########################################################


async def test_list_project_importations_200_ok_owner_no_importation(client):
    workspace = await f.create_workspace()
    client.login(workspace.created_by)
    response = await client.get(f"/workspaces/{workspace.b64id}/projects/importations")
    assert response.status_code == 200, response.data["data"]
    assert response.data == {"data": []}


async def test_list_project_importations_200_ok_owner_one_project(client):
    importation = await f.create_project_importation(project=None)

    client.login(importation.workspace.created_by)
    response = await client.get(
        f"/workspaces/{importation.workspace.b64id}/projects/importations"
    )
    assert response.status_code == 200, response.data["data"]
    res = response.data["data"]
    assert len(res) == 1
    assert res[0]["id"] == importation.b64id
    assert res[0]["status"] == ImportationStatus.PENDING


async def test_list_project_importations_404_not_found_workspace_b64id(client):
    user = await f.create_user()
    client.login(user)
    response = await client.get(
        f"/workspaces/{NOT_EXISTING_B64ID}/projects/importations"
    )
    assert response.status_code == 404, response.text


async def test_list_project_importations_422_unprocessable_workspace_b64id(client):
    user = await f.create_user()
    client.login(user)
    response = await client.get(f"/workspaces/{INVALID_B64ID}/projects/importations")
    assert response.status_code == 422, response.data


##########################################################
# DELETE /projects/importations/<id>
##########################################################


@pytest.mark.django_db(transaction=True)
async def test_delete_project_importation_204_no_content_being_importation_creator(
    client,
):
    # without project
    project_importation = await f.create_project_importation(
        status=ImportationStatus.FAILURE, project=None
    )

    client.login(project_importation.created_by)
    response = await client.delete(
        f"/projects/importations/{project_importation.b64id}"
    )
    assert response.status_code == 204, response.data

    # with project
    project_importation = await f.create_project_importation(
        status=ImportationStatus.FAILURE,
    )

    client.login(project_importation.created_by)
    response = await client.delete(
        f"/projects/importations/{project_importation.b64id}"
    )
    assert response.status_code == 204, response.data
    with pytest.raises(Project.DoesNotExist):
        await project_importation.project.arefresh_from_db()


async def test_delete_project_importation_403_forbidden_not_creator(client):
    project_importation = await f.create_project_importation(
        status=ImportationStatus.FAILURE, project=None
    )
    user = await f.create_user()

    client.login(user)
    response = await client.delete(
        f"/projects/importations/{project_importation.b64id}"
    )
    assert response.status_code == 403, response.data


async def test_delete_project_importation_400_bad_request_invalid_status(client):
    project_importation = await f.create_project_importation(
        status=ImportationStatus.SUCCESS, project=None
    )

    client.login(project_importation.created_by)
    response = await client.delete(
        f"/projects/importations/{project_importation.b64id}"
    )
    assert response.status_code == 400, response.data

    project_importation = await f.create_project_importation(
        status=ImportationStatus.ACTION_NEEDED,
        project=None,
        created_by=project_importation.created_by,
    )

    client.login(project_importation.created_by)
    response = await client.delete(
        f"/projects/importations/{project_importation.b64id}"
    )
    assert response.status_code == 400, response.data


async def test_delete_project_importation_404_not_found_project_b64id(client):
    user = await f.create_user()
    client.login(user)
    response = await client.delete(f"/projects/importations/{NOT_EXISTING_B64ID}")
    assert response.status_code == 404, response.data


async def test_delete_project_importation_422_unprocessable_project_b64id(client):
    user = await f.create_user()
    client.login(user)
    response = await client.delete(f"/projects/importations/{INVALID_B64ID}")
    assert response.status_code == 422, response.data
