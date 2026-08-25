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
from base64 import b64encode
from datetime import timedelta
from operator import attrgetter
from unittest.mock import Mock, patch

import boto3
import pytest
from botocore.exceptions import ClientError
from django.conf import settings
from django.test import override_settings
from zoneinfo import ZoneInfo

from commons.storage.models import TusUpload
from import_export.models import (
    ImportationStatus,
    ProjectImportation,
    ProjectImportationType,
)
from projects.projects.models import Project
from tests.commons.storage.utils import S3_STORAGE_SETTINGS, patch_s3_multipart_upload
from tests.utils import factories as f
from tests.utils.bad_params import INVALID_B64ID, NOT_EXISTING_B64ID

pytestmark = pytest.mark.django_db


##########################################################
# POST /workspaces/<id>/projects/importation
##########################################################


@patch.object(settings.STORAGE, "IMPORTATION_MAX_UPLOAD_FILE_SIZE", 10)
@patch.object(settings.STORAGE, "TUS_UPLOAD_EXPIRATION", 2)
async def test_launch_importation_200_deferred_content(client):
    workspace = await f.create_workspace()

    client.login(workspace.created_by)
    # test with no content and partial content
    for content_length, data in [(0, None), (2, b"{}")]:
        response = await client.post(
            f"/workspaces/{workspace.b64id}/projects/importations",
            data=data,
            headers={
                "Tus-Resumable": settings.SUPPORTED_TUS_VERSION,
                "Upload-Metadata": "originType VEE=,filename Zm9vLmpzb24=,filetype YXBwbGljYXRpb24vanNvbg==",
                "Content-Type": "application/offset+octet-stream",
                "Upload-Length": 5,
                "Content-Length": content_length,
            },
        )
        assert response.status_code == 201, response.data

        assert not await ProjectImportation.objects.aexists()
        tus_upload = await TusUpload.objects.aget()
        assert tus_upload.created_by_id == workspace.created_by_id

        assert (
            response.headers["Tus-Resumable"]
            == response.headers["Tus-Version"]
            == settings.SUPPORTED_TUS_VERSION
        )
        assert response.headers["Tus-Extension"] == settings.SUPPORTED_TUS_EXTENSIONS
        assert response.headers["Tus-Max-Size"] == "10"
        assert response.headers["Upload-Offset"] == str(content_length)
        assert response.headers["Upload-Length"] == "5"
        assert response.headers["Location"].endswith(f"/upload/{tus_upload.b64id}")
        gmt_expiration = (tus_upload.created_at + timedelta(hours=2)).astimezone(
            ZoneInfo("GMT")
        )
        assert response.headers["Upload-Expires"] == gmt_expiration.strftime(
            "%a, %d %b %Y %H:%M:%S %Z"
        )
        await TusUpload.objects.all().adelete()


@patch.object(settings.STORAGE, "IMPORTATION_MAX_UPLOAD_FILE_SIZE", 10)
@patch.object(settings.STORAGE, "TUS_UPLOAD_EXPIRATION", 2)
async def test_launch_importation_200_full_content(client):
    workspace = await f.create_workspace()

    client.login(workspace.created_by)
    response = await client.post(
        f"/workspaces/{workspace.b64id}/projects/importations",
        data=b"{}",
        headers={
            "Tus-Resumable": settings.SUPPORTED_TUS_VERSION,
            "Upload-Metadata": "originType VEE=,filename Zm9vLmpzb24=,filetype YXBwbGljYXRpb24vanNvbg==",
            "Content-Type": "application/offset+octet-stream",
            "Upload-Length": 5,
            "Content-Length": 5,
        },
    )
    assert response.status_code == 201, response.data

    importation = await ProjectImportation.objects.aget()
    assert importation.status == ImportationStatus.PENDING
    assert importation.workspace_id == workspace.id
    assert importation.pending_invites == {}
    # check that the file has been moved to the correct folder
    assert importation.source.name.startswith("project/importation")

    assert not await TusUpload.objects.aexists()

    assert (
        response.headers["Tus-Resumable"]
        == response.headers["Tus-Version"]
        == settings.SUPPORTED_TUS_VERSION
    )
    assert response.headers["Tus-Extension"] == settings.SUPPORTED_TUS_EXTENSIONS
    assert response.headers["Tus-Max-Size"] == "10"
    assert response.headers["Upload-Offset"] == "2"
    assert response.headers["Upload-Length"] == "5"


async def test_launch_importation_404_not_found_workspace_error(client):
    workspace = await f.create_workspace()

    client.login(workspace.created_by)
    response = await client.post(
        f"/workspaces/{NOT_EXISTING_B64ID}/projects/importations",
        data=b"{}",
        headers={
            "Tus-Resumable": settings.SUPPORTED_TUS_VERSION,
            "Upload-Metadata": "originType VEE=,filename Zm9vLmpzb24=,filetype YXBwbGljYXRpb24vanNvbg==",
            "Content-Type": "application/offset+octet-stream",
            "Upload-Length": 5,
            "Content-Length": 5,
        },
    )
    assert response.status_code == 404, response.data


async def test_launch_importation_403_being_no_workspace_member(client):
    workspace = await f.create_workspace()
    user2 = await f.create_user()

    client.login(user2)
    response = await client.post(
        f"/workspaces/{workspace.b64id}/projects/importations",
        data=b"{}",
        headers={
            "Tus-Resumable": settings.SUPPORTED_TUS_VERSION,
            "Upload-Metadata": "originType VEE=,filename Zm9vLmpzb24=,filetype YXBwbGljYXRpb24vanNvbg==",
            "Content-Type": "application/offset+octet-stream",
            "Upload-Length": 5,
            "Content-Length": 5,
        },
    )
    assert response.status_code == 403, response.data


async def test_launch_importation_401_being_anonymous(client):
    workspace = await f.create_workspace()

    response = await client.post(
        f"/workspaces/{workspace.b64id}/projects/importations",
    )
    assert response.status_code == 401, response.data


async def test_launch_importation_422_unprocessable_file(client):
    workspace = await f.create_workspace()

    client.login(workspace.created_by)
    response = await client.post(
        f"/workspaces/{workspace.b64id}/projects/importations",
        data=b"{}",
        headers={
            "Tus-Resumable": settings.SUPPORTED_TUS_VERSION,
            "Upload-Metadata": f"originType VEE=,filename Zm9vLmpzb24=,filetype {b64encode(bytes('image/png', 'utf-8'))}",
            "Content-Type": "application/offset+octet-stream",
            "Upload-Length": 5,
            "Content-Length": 5,
        },
    )
    assert response.status_code == 422, response.data


async def test_launch_importation_422_unprocessable_uuid(client):
    workspace = await f.create_workspace()

    client.login(workspace.created_by)
    response = await client.post(
        f"/workspaces/{INVALID_B64ID}/projects/importations",
        data=b"{}",
        headers={
            "Tus-Resumable": settings.SUPPORTED_TUS_VERSION,
            "Upload-Metadata": "originType VEE=,filename Zm9vLmpzb24=,filetype YXBwbGljYXRpb24vanNvbg==",
            "Content-Type": "application/offset+octet-stream",
            "Upload-Length": 5,
            "Content-Length": 5,
        },
    )
    assert response.status_code == 422, response.data


async def test_terminate_tus_upload_412(client):
    workspace = await f.create_workspace()

    client.login(workspace.created_by)

    response = await client.post(
        f"/workspaces/{workspace.b64id}/projects/importations",
        data=b"{}",
        headers={
            "Tus-Resumable": "invalid",
            "Upload-Metadata": "originType VEE=,filename Zm9vLmpzb24=,filetype YXBwbGljYXRpb24vanNvbg==",
            "Content-Type": "application/offset+octet-stream",
            "Upload-Length": 5,
            "Content-Length": 5,
        },
    )
    assert response.status_code == 412, response.data
    assert response.headers["Tus-Version"] == settings.SUPPORTED_TUS_VERSION


async def test_terminate_tus_upload_400_size(client):
    workspace = await f.create_workspace()

    client.login(workspace.created_by)

    response = await client.post(
        f"/workspaces/{workspace.b64id}/projects/importations",
        data=b"{}",
        headers={
            "Tus-Resumable": settings.SUPPORTED_TUS_VERSION,
            "Upload-Metadata": "originType VEE=,filename Zm9vLmpzb24=,filetype YXBwbGljYXRpb24vanNvbg==",
            "Content-Type": "application/offset+octet-stream",
            "Upload-Length": 5,
            "Content-Length": 6,
        },
    )
    # announced content-length bigger than upload-length
    assert response.status_code == 400, response.data


async def test_terminate_tus_upload_413(client):
    workspace = await f.create_workspace()

    client.login(workspace.created_by)

    response = await client.post(
        f"/workspaces/{workspace.b64id}/projects/importations",
        data=b"{}",
        headers={
            "Tus-Resumable": settings.SUPPORTED_TUS_VERSION,
            "Upload-Metadata": "originType VEE=,filename Zm9vLmpzb24=,filetype YXBwbGljYXRpb24vanNvbg==",
            "Content-Type": "application/offset+octet-stream",
            "Upload-Length": settings.STORAGE.IMPORTATION_MAX_UPLOAD_FILE_SIZE + 1,
            "Content-Length": 5,
        },
    )
    # upload size exceeds max allowed size
    assert response.status_code == 413, response.data

    assert response.headers["Tus-Max-Size"] == str(
        settings.STORAGE.IMPORTATION_MAX_UPLOAD_FILE_SIZE
    )
    response = await client.post(
        f"/workspaces/{workspace.b64id}/projects/importations",
        data=b"a" * 7,
        headers={
            "Tus-Resumable": settings.SUPPORTED_TUS_VERSION,
            "Upload-Metadata": "originType VEE=,filename Zm9vLmpzb24=,filetype YXBwbGljYXRpb24vanNvbg==",
            "Content-Type": "application/offset+octet-stream",
            "Upload-Length": 6,
            "Content-Length": 6,
        },
    )
    # concrete content length overflow the total_size of the tus_upload
    assert response.status_code == 413, response.data
    assert response.headers["Tus-Max-Size"] == "6"


@override_settings(**{"STORAGES": S3_STORAGE_SETTINGS})
async def test_terminate_tus_upload_424_multipart(client):
    workspace = await f.create_workspace()

    s3 = boto3.resource("s3")
    mock_upload = Mock(
        spec=s3.MultipartUploadPart("", "", "", 1).upload,
        side_effect=ClientError({}, ""),
    )
    file_field = TusUpload._meta.get_field("file")
    storage = file_field.storage

    client.login(workspace.created_by)

    with (
        patch_s3_multipart_upload(mock_upload=mock_upload) as multipart_mocks,
        patch.object(
            storage, "get_available_name", autospec=True
        ) as fake_get_available_name,
        patch.object(storage, "_open", autospec=True) as fake_storage_open,
    ):
        fake_storage_open.return_value.obj.key = "test_key"
        fake_storage_open.return_value.obj.initiate_multipart_upload.return_value.id = (
            "test_id"
        )
        response = await client.post(
            f"/workspaces/{workspace.b64id}/projects/importations",
            data=b"{}",
            headers={
                "Tus-Resumable": settings.SUPPORTED_TUS_VERSION,
                "Upload-Metadata": "originType VEE=,filename Zm9vLmpzb24=,filetype YXBwbGljYXRpb24vanNvbg==",
                "Content-Type": "application/offset+octet-stream",
                "Upload-Length": 6,
                "Content-Length": 6,
            },
        )
    assert response.status_code == 424, response.data


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
    # pending without project
    project_importation = await f.create_project_importation(
        status=ImportationStatus.PENDING, project=None
    )

    client.login(project_importation.created_by)
    response = await client.delete(
        f"/projects/importations/{project_importation.b64id}"
    )
    assert response.status_code == 204, response.data

    # failure with project
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


async def test_delete_project_importation_404_not_found_importation_b64id(client):
    user = await f.create_user()
    client.login(user)
    response = await client.delete(f"/projects/importations/{NOT_EXISTING_B64ID}")
    assert response.status_code == 404, response.data


async def test_delete_project_importation_422_unprocessable_importation_b64id(client):
    user = await f.create_user()
    client.login(user)
    response = await client.delete(f"/projects/importations/{INVALID_B64ID}")
    assert response.status_code == 422, response.data


##########################################################
# POST /projects/importations/<id>/invite
##########################################################


async def test_handle_project_importation_pending_invites_200_being_importation_creator(
    client, project_template
):
    project = await f.create_project(project_template)
    project_importation = await f.create_project_importation(
        status=ImportationStatus.ACTION_NEEDED,
        project=project,
        created_by=project.created_by,
    )
    roles = list(project_importation.project.roles.all())
    owner_role = next(filter(attrgetter("is_owner"), roles))
    member_role = next(filter(lambda role: role.slug == "member", roles))
    data = {
        "invitations": [
            {"email": "test@email.com", "role_id": owner_role.b64id},
            {"email": "test2@email.com", "role_id": member_role.b64id},
        ]
    }

    client.login(project_importation.created_by)
    response = await client.post(
        f"/projects/importations/{project_importation.b64id}/invite", json=data
    )
    assert response.status_code == 200, response.data
    assert len(response.data["invitations"]) == 2
    assert response.data["projectImportation"]["id"] == project_importation.b64id
    assert response.data["projectImportation"]["status"] == ImportationStatus.SUCCESS


@pytest.mark.django_db(transaction=True)
async def test_handle_project_importation_pending_invites_empty_200_being_importation_creator(
    client,
):
    project_importation = await f.create_project_importation(
        status=ImportationStatus.ACTION_NEEDED,
    )
    data = {"invitations": []}

    client.login(project_importation.created_by)
    response = await client.post(
        f"/projects/importations/{project_importation.b64id}/invite", json=data
    )
    assert response.status_code == 200, response.data
    assert not response.data["invitations"]
    assert response.data["projectImportation"]["id"] == project_importation.b64id
    assert response.data["projectImportation"]["status"] == ImportationStatus.SUCCESS


async def test_handle_project_importation_pending_invites_403_forbidden_not_creator(
    client,
):
    project_importation = await f.create_project_importation(
        status=ImportationStatus.ACTION_NEEDED, project=None
    )
    user = await f.create_user()
    data = {"invitations": []}

    client.login(user)
    response = await client.post(
        f"/projects/importations/{project_importation.b64id}/invite", json=data
    )
    assert response.status_code == 403, response.data


async def test_handle_project_importation_pending_invites_400_bad_request_invalid_status(
    client,
):
    project_importation = await f.create_project_importation(
        status=ImportationStatus.SUCCESS, project=None
    )
    data = {"invitations": []}

    client.login(project_importation.created_by)
    response = await client.post(
        f"/projects/importations/{project_importation.b64id}/invite", json=data
    )
    assert response.status_code == 400, response.data

    project_importation = await f.create_project_importation(
        status=ImportationStatus.ONGOING,
        project=None,
        created_by=project_importation.created_by,
    )

    client.login(project_importation.created_by)
    response = await client.post(
        f"/projects/importations/{project_importation.b64id}/invite", json=data
    )
    assert response.status_code == 400, response.data


async def test_handle_project_importation_pending_invites_404_not_found_importation_b64id(
    client,
):
    user = await f.create_user()
    client.login(user)
    data = {"invitations": []}
    response = await client.post(
        f"/projects/importations/{NOT_EXISTING_B64ID}/invite", json=data
    )
    assert response.status_code == 404, response.data


async def test_handle_project_importation_pending_invites_422_unprocessable_importation_b64id(
    client,
):
    user = await f.create_user()
    client.login(user)
    data = {"invitations": []}
    response = await client.post(
        f"/projects/importations/{INVALID_B64ID}/invite", json=data
    )
    assert response.status_code == 422, response.data
