# Copyright (C) 2026 BIRU
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
from datetime import timedelta
from unittest.mock import MagicMock, Mock, patch

import boto3
import pytest
from botocore.exceptions import ClientError
from django.conf import settings
from django.test import override_settings
from redis.exceptions import LockError
from zoneinfo import ZoneInfo

from commons.exceptions import api as ex
from commons.storage.api import add_tus_headers, check_tus_request
from commons.storage.models import S3PendingUploadData, TusUpload
from ninja_jwt.utils import aware_utcnow
from tests.commons.storage.utils import S3_STORAGE_SETTINGS, patch_s3_multipart_upload
from tests.utils import factories as f
from tests.utils.bad_params import INVALID_B64ID, NOT_EXISTING_B64ID

pytestmark = pytest.mark.django_db

##########################################################
# HEAD /upload/<id>
##########################################################


async def test_check_tus_upload_401_403(client):
    tus_upload = await f.create_tus_upload()

    response = await client.head(
        f"/upload/{tus_upload.b64id}",
    )
    assert response.status_code == 401, response.data
    client.login(await f.create_user())
    response = await client.head(
        f"/upload/{tus_upload.b64id}",
        headers={"Tus-Resumable": settings.SUPPORTED_TUS_VERSION},
    )
    assert response.status_code == 403, response.data


async def test_check_tus_upload_422(client):
    client.login(await f.create_user())
    response = await client.head(
        f"/upload/{INVALID_B64ID}",
        headers={"Tus-Resumable": settings.SUPPORTED_TUS_VERSION},
    )
    assert response.status_code == 422, response.data


async def test_check_tus_upload_404(client):
    client.login(await f.create_user())
    response = await client.head(
        f"/upload/{NOT_EXISTING_B64ID}",
        headers={"Tus-Resumable": settings.SUPPORTED_TUS_VERSION},
    )
    assert response.status_code == 404, response.data


@patch.object(settings.STORAGE, "IMPORTATION_MAX_UPLOAD_FILE_SIZE", 3)
@patch.object(settings.STORAGE, "TUS_UPLOAD_EXPIRATION", 2)
async def test_check_tus_upload_ok(client):
    now = aware_utcnow()
    tus_upload = await f.create_tus_upload(offset=4, total_size=10, created_at=now)

    client.login(tus_upload.created_by)
    response = await client.head(
        f"/upload/{tus_upload.b64id}",
        headers={"Tus-Resumable": settings.SUPPORTED_TUS_VERSION},
    )
    assert response.status_code == 200, response.data
    assert (
        response.headers["Tus-Resumable"]
        == response.headers["Tus-Version"]
        == settings.SUPPORTED_TUS_VERSION
    )
    assert response.headers["Tus-Extension"] == settings.SUPPORTED_TUS_EXTENSIONS
    assert response.headers["Tus-Max-Size"] == "3"
    assert response.headers["Upload-Offset"] == "4"
    assert response.headers["Upload-Length"] == "10"
    assert response.headers["Location"].endswith(f"/upload/{tus_upload.b64id}")
    gmt_expiration = (now + timedelta(hours=2)).astimezone(ZoneInfo("GMT"))
    assert response.headers["Upload-Expires"] == gmt_expiration.strftime(
        "%a, %d %b %Y %H:%M:%S %Z"
    )


##########################################################
# PATCH /upload/<id>
##########################################################


async def test_continue_tus_upload_401_403(client):
    tus_upload = await f.create_tus_upload()

    response = await client.patch(
        f"/upload/{tus_upload.b64id}",
    )
    assert response.status_code == 401, response.data
    client.login(await f.create_user())
    response = await client.patch(
        f"/upload/{tus_upload.b64id}",
        headers={
            "Tus-Resumable": settings.SUPPORTED_TUS_VERSION,
            "Content-Type": "application/offset+octet-stream",
            "Upload-Offset": 0,
            "Content-Length": 5,
        },
    )
    assert response.status_code == 403, response.data


async def test_continue_tus_upload_422(client):
    tus_upload = await f.create_tus_upload()

    client.login(tus_upload.created_by)
    response = await client.patch(
        f"/upload/{tus_upload.b64id}",
        data=b"a",
        headers={"Tus-Resumable": settings.SUPPORTED_TUS_VERSION},
    )
    assert response.status_code == 422, response.data


async def test_continue_tus_upload_404(client):
    client.login(await f.create_user())
    response = await client.patch(
        f"/upload/{NOT_EXISTING_B64ID}",
        headers={
            "Tus-Resumable": settings.SUPPORTED_TUS_VERSION,
            "Content-Type": "application/offset+octet-stream",
            "Upload-Offset": 0,
            "Content-Length": 5,
        },
    )
    assert response.status_code == 404, response.data


@patch.object(settings.STORAGE, "IMPORTATION_MAX_UPLOAD_FILE_SIZE", 3)
@patch.object(settings.STORAGE, "TUS_UPLOAD_EXPIRATION", 2)
async def test_continue_tus_upload_ok(client):
    now = aware_utcnow()
    tus_upload = await f.create_tus_upload(offset=4, total_size=10, created_at=now)

    client.login(tus_upload.created_by)
    response = await client.patch(
        f"/upload/{tus_upload.b64id}",
        data=b"a" * 5,
        headers={
            "Tus-Resumable": settings.SUPPORTED_TUS_VERSION,
            "Content-Type": "application/offset+octet-stream",
            "Upload-Offset": tus_upload.offset,
            "Content-Length": 5,
        },
    )
    assert response.status_code == 204, response.data
    assert (
        response.headers["Tus-Resumable"]
        == response.headers["Tus-Version"]
        == settings.SUPPORTED_TUS_VERSION
    )
    assert response.headers["Tus-Extension"] == settings.SUPPORTED_TUS_EXTENSIONS
    assert response.headers["Tus-Max-Size"] == "3"
    assert response.headers["Upload-Offset"] == "9"
    assert response.headers["Upload-Length"] == "10"
    gmt_expiration = (now + timedelta(hours=2)).astimezone(ZoneInfo("GMT"))
    assert response.headers["Upload-Expires"] == gmt_expiration.strftime(
        "%a, %d %b %Y %H:%M:%S %Z"
    )


async def test_continue_tus_upload_409(client):
    tus_upload = await f.create_tus_upload(offset=4, total_size=10)

    client.login(tus_upload.created_by)
    response = await client.patch(
        f"/upload/{tus_upload.b64id}",
        data=b"a",
        headers={
            "Tus-Resumable": settings.SUPPORTED_TUS_VERSION,
            "Content-Type": "application/offset+octet-stream",
            "Upload-Offset": tus_upload.offset + 1,
            "Content-Length": 5,
        },
    )
    assert response.status_code == 409, response.data


async def test_continue_tus_upload_413(client):
    tus_upload = await f.create_tus_upload(offset=4, total_size=10)

    client.login(tus_upload.created_by)
    response = await client.patch(
        f"/upload/{tus_upload.b64id}",
        data=b"a" * 5,
        headers={
            "Tus-Resumable": settings.SUPPORTED_TUS_VERSION,
            "Content-Type": "application/offset+octet-stream",
            "Upload-Offset": tus_upload.offset,
            "Content-Length": 7,
        },
    )
    # announced content-length overflow the total_size of the tus_upload
    assert response.status_code == 413, response.data
    assert response.headers["Tus-Max-Size"] == str(tus_upload.total_size)
    response = await client.patch(
        f"/upload/{tus_upload.b64id}",
        data=b"a" * 7,
        headers={
            "Tus-Resumable": settings.SUPPORTED_TUS_VERSION,
            "Content-Type": "application/offset+octet-stream",
            "Upload-Offset": tus_upload.offset,
            "Content-Length": 5,
        },
    )
    # concrete content length overflow the total_size of the tus_upload
    assert response.status_code == 413, response.data
    assert response.headers["Tus-Max-Size"] == str(tus_upload.total_size)


@override_settings(**{"STORAGES": S3_STORAGE_SETTINGS})
async def test_continue_tus_upload_404_multipart(client):
    tus_upload = await f.create_tus_upload(
        file=None,
        pending_upload_data=S3PendingUploadData(
            upload_id="test_id", object_key="test_key"
        ),
        offset=4,
        total_size=10,
    )

    file_field = TusUpload._meta.get_field("file")
    storage = file_field.storage
    s3 = boto3.resource("s3")
    mock_parts = MagicMock(
        spec=s3.MultipartUpload("", "", "").parts,
        **{
            "all.side_effect": storage.connection.meta.client.exceptions.NoSuchUpload(
                {}, ""
            )
        },
    )

    client.login(tus_upload.created_by)
    with (
        patch_s3_multipart_upload(mock_parts=mock_parts),
        patch.object(storage, "delete"),
    ):
        response = await client.patch(
            f"/upload/{tus_upload.b64id}",
            data=b"a" * 5,
            headers={
                "Tus-Resumable": settings.SUPPORTED_TUS_VERSION,
                "Content-Type": "application/offset+octet-stream",
                "Upload-Offset": tus_upload.offset,
                "Content-Length": 5,
            },
        )
    assert response.status_code == 404, response.data


@override_settings(**{"STORAGES": S3_STORAGE_SETTINGS})
async def test_continue_tus_upload_424_multipart(client):
    tus_upload = await f.create_tus_upload(
        file=None,
        pending_upload_data=S3PendingUploadData(
            upload_id="test_id", object_key="test_key"
        ),
        offset=4,
        total_size=10,
    )

    s3 = boto3.resource("s3")
    mock_upload = Mock(
        spec=s3.MultipartUploadPart("", "", "", 1).upload,
        side_effect=ClientError({}, ""),
    )

    client.login(tus_upload.created_by)
    with (
        patch_s3_multipart_upload(mock_upload=mock_upload) as multipart_mocks,
    ):
        response = await client.patch(
            f"/upload/{tus_upload.b64id}",
            data=b"a" * 5,
            headers={
                "Tus-Resumable": settings.SUPPORTED_TUS_VERSION,
                "Content-Type": "application/offset+octet-stream",
                "Upload-Offset": tus_upload.offset,
                "Content-Length": 5,
            },
        )
    assert response.status_code == 424, response.data


async def test_continue_tus_upload_423(client):
    tus_upload = await f.create_tus_upload(offset=4, total_size=10)

    client.login(tus_upload.created_by)
    with patch("base.utils.concurrency.aget_redis_lock", side_effect=LockError):
        response = await client.patch(
            f"/upload/{tus_upload.b64id}",
            data=b"a" * 5,
            headers={
                "Tus-Resumable": settings.SUPPORTED_TUS_VERSION,
                "Content-Type": "application/offset+octet-stream",
                "Upload-Offset": tus_upload.offset,
                "Content-Length": 5,
            },
        )
    assert response.status_code == 423, response.data


##########################################################
# DELETE /upload/<id>
##########################################################


async def test_terminate_tus_upload_401_403(client):
    tus_upload = await f.create_tus_upload()

    response = await client.delete(
        f"/upload/{tus_upload.b64id}",
    )
    assert response.status_code == 401, response.data
    client.login(await f.create_user())
    response = await client.delete(
        f"/upload/{tus_upload.b64id}",
        headers={"Tus-Resumable": settings.SUPPORTED_TUS_VERSION},
    )
    assert response.status_code == 403, response.data


async def test_terminate_tus_upload_422(client):
    client.login(await f.create_user())
    response = await client.delete(
        f"/upload/{INVALID_B64ID}",
        data=b"a",
        headers={"Tus-Resumable": settings.SUPPORTED_TUS_VERSION},
    )
    assert response.status_code == 422, response.data


async def test_terminate_tus_upload_404(client):
    client.login(await f.create_user())
    response = await client.delete(
        f"/upload/{NOT_EXISTING_B64ID}",
        headers={"Tus-Resumable": settings.SUPPORTED_TUS_VERSION},
    )
    assert response.status_code == 404, response.data


async def test_terminate_tus_upload_412(client):
    tus_upload = await f.create_tus_upload(offset=4, total_size=10)

    client.login(tus_upload.created_by)
    response = await client.delete(f"/upload/{tus_upload.b64id}", data=b"a" * 5)
    assert response.status_code == 412, response.data
    assert response.headers["Tus-Version"] == settings.SUPPORTED_TUS_VERSION


async def test_terminate_tus_upload_ok(client):
    tus_upload = await f.create_tus_upload(offset=4, total_size=10)

    client.login(tus_upload.created_by)
    response = await client.delete(
        f"/upload/{tus_upload.b64id}",
        headers={"Tus-Resumable": settings.SUPPORTED_TUS_VERSION},
    )
    assert response.status_code == 204, response.data
    assert not await TusUpload.objects.filter(id=tus_upload.id).aexists()


async def test_terminate_tus_upload_423(client):
    tus_upload = await f.create_tus_upload(offset=4, total_size=10)

    client.login(tus_upload.created_by)
    with patch("base.utils.concurrency.aget_redis_lock", side_effect=LockError):
        response = await client.delete(
            f"/upload/{tus_upload.b64id}",
            data=b"a" * 5,
            headers={
                "Tus-Resumable": settings.SUPPORTED_TUS_VERSION,
                "Content-Type": "application/offset+octet-stream",
                "Upload-Offset": tus_upload.offset,
                "Content-Length": 5,
            },
        )
    assert response.status_code == 423, response.data


##########################################################
# misc
##########################################################


@override_settings(
    SUPPORTED_TUS_VERSION="test-version", SUPPORTED_TUS_EXTENSIONS="test-extensions"
)
@patch.object(settings.STORAGE, "TUS_UPLOAD_EXPIRATION", 2)
def test_add_tus_headers():
    now = aware_utcnow()
    tus_upload = f.build_tus_upload(offset=4, total_size=10, created_at=now)
    response = Mock(headers={})

    add_tus_headers(response, tus_upload)

    assert (
        response.headers["Tus-Resumable"]
        == response.headers["Tus-Version"]
        == "test-version"
    )
    assert response.headers["Tus-Extension"] == "test-extensions"
    assert "Tus-Max-Size" not in response.headers
    assert response.headers["Upload-Offset"] == 4
    assert response.headers["Upload-Length"] == 10
    assert response.headers["Location"].endswith(f"/upload/{tus_upload.b64id}")
    gmt_expiration = (now + timedelta(hours=2)).astimezone(ZoneInfo("GMT"))
    assert response.headers["Upload-Expires"] == gmt_expiration.strftime(
        "%a, %d %b %Y %H:%M:%S %Z"
    )

    add_tus_headers(response, tus_upload, max_size=3)
    assert response.headers["Tus-Max-Size"] == 3


def test_check_tus_request_version():
    request = Mock(headers={})

    with pytest.raises(ex.PreconditionFailed):
        check_tus_request(request)
    request.headers["Tus-Resumable"] = "invalid"

    with pytest.raises(ex.PreconditionFailed):
        check_tus_request(request)

    request.headers["Tus-Resumable"] = settings.SUPPORTED_TUS_VERSION
    check_tus_request(request)


def test_check_tus_request_size():
    request = Mock(
        headers={"Tus-Resumable": settings.SUPPORTED_TUS_VERSION, "Upload-Length": 3}
    )
    # OK if upload-length and no max size
    check_tus_request(request)

    with pytest.raises(ex.ContentTooLarge):
        # KO if upload-length > max size
        check_tus_request(request, max_size=2)
    request.headers["Content-Length"] = 6
    with pytest.raises(ex.BadRequest):
        # KO if content-length > upload-length
        check_tus_request(request, max_size=4)
    # OK if upload-length, content-length and no max size
    check_tus_request(request)

    # OK if upload-length badly formated
    request.headers["Upload-Length"] = "not-a-number"
    check_tus_request(request, max_size=4)


def test_check_tus_request_contenttype():
    request = Mock(headers={"Tus-Resumable": settings.SUPPORTED_TUS_VERSION})
    # OK if no content-type
    check_tus_request(request)

    request.headers["Content-Type"] = "invalid"
    with pytest.raises(ex.UnsupportedMediaType):
        # KO if invalid content-type
        check_tus_request(request)
    # OK if valid content-type
    request.headers["Content-Type"] = "application/offset+octet-stream"
    check_tus_request(request)
