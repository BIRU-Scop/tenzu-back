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

from import_export.models import ImportationStatus, ImportationType
from tests.utils import factories as f
from tests.utils.bad_params import INVALID_B64ID, NOT_EXISTING_B64ID

pytestmark = pytest.mark.django_db


##########################################################
# POST /workspaces/<id>/projects/importation
##########################################################


async def test_launch_importation_200_ok_being_workspace_member(client):
    workspace = await f.create_workspace()
    data = {
        "originType": ImportationType.TAIGA,
        "source": f.build_string_uploadfile("taiga_export", "json", "application/json"),
    }

    client.login(workspace.created_by)
    response = await client.post(
        f"/workspaces/{workspace.b64id}/projects/importation",
        data=data,  # , files=files
    )
    assert response.status_code == 200, response.data["data"]
    res = response.data["data"]
    assert res["originType"] == data["originType"]
    assert res["status"] == ImportationStatus.PENDING
    assert res["errorResultFile"] is None
    assert res["extraData"]["workspace_id"] == workspace.b64id


async def test_launch_importation_404_not_found_workspace_error(client):
    workspace = await f.create_workspace()
    data = {
        "originType": ImportationType.TAIGA,
        "source": f.build_string_uploadfile("taiga_export", "json", "application/json"),
    }

    client.login(workspace.created_by)
    response = await client.post(
        f"/workspaces/{NOT_EXISTING_B64ID}/projects/importation", data=data
    )
    assert response.status_code == 404, response.data


async def test_launch_importation_403_being_no_workspace_member(client):
    workspace = await f.create_workspace()
    user2 = await f.create_user()
    data = {
        "originType": ImportationType.TAIGA,
        "source": f.build_string_uploadfile("taiga_export", "json", "application/json"),
    }

    client.login(user2)
    response = await client.post(
        f"/workspaces/{workspace.b64id}/projects/importation", data=data
    )
    assert response.status_code == 403, response.data


async def test_launch_importation_401_being_anonymous(client):
    workspace = await f.create_workspace()
    data = {
        "originType": ImportationType.TAIGA,
        "source": f.build_string_uploadfile("taiga_export", "json", "application/json"),
    }

    response = await client.post(
        f"/workspaces/{workspace.b64id}/projects/importation", data=data
    )
    assert response.status_code == 401, response.data


async def test_launch_importation_422_unprocessable_file(client):
    workspace = await f.create_workspace()
    data = {
        "originType": ImportationType.TAIGA,
        "source": f.build_image_uploadfile("taiga_export", "png", "image/png"),
    }

    client.login(workspace.created_by)
    response = await client.post(
        f"/workspaces/{workspace.b64id}/projects/importation", data=data
    )
    assert response.status_code == 422, response.data


async def test_launch_importation_422_unprocessable_uuid(client):
    workspace = await f.create_workspace()
    data = {
        "originType": ImportationType.TAIGA,
        "source": f.build_string_uploadfile("taiga_export", "json", "application/json"),
    }

    client.login(workspace.created_by)
    response = await client.post(
        f"/workspaces/{INVALID_B64ID}/projects/importation", data=data
    )
    assert response.status_code == 422, response.data
