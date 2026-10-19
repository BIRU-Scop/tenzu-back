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
import re
from datetime import timedelta
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import boto3
import pytest
from botocore.exceptions import ClientError
from django.test import TestCase, override_settings

from commons.storage import exceptions as ex
from commons.storage import repositories
from commons.storage.models import S3Part, S3PendingUploadData, TusUpload
from configurations.utils import KILOBYTE
from ninja_jwt.utils import aware_utcnow
from tests.commons.storage.utils import S3_STORAGE_SETTINGS, patch_s3_multipart_upload
from tests.utils import factories as f

pytestmark = pytest.mark.django_db


##########################################################
# storaged object
########################################################


def test_delete_storaged_object():
    storaged_object = f.StoragedObjectFactory.create()
    path = storaged_object.file.path
    assert Path(path).exists()

    with TestCase.captureOnCommitCallbacks(execute=True) as callbacks:
        assert repositories.delete_storaged_object(storaged_object)
    assert not Path(path).exists()


##########################################################
# tus upload
########################################################


async def test_get_tus_upload():
    tus_upload = await f.create_tus_upload()
    assert await repositories.get_tus_upload(tus_upload.id) == tus_upload


def test_list_tus_uploads():
    now = aware_utcnow()
    present_tus_upload = f.TusUploadFactory.create(created_at=now)
    past_tus_upload = f.TusUploadFactory.create(created_at=now - timedelta(hours=1))
    future_tus_upload = f.TusUploadFactory.create(created_at=now + timedelta(hours=1))
    assert repositories.list_tus_uploads({"created_at__lt": now}) == [past_tus_upload]


@pytest.mark.parametrize(
    "overwrite_base_path, result_base_path",
    [
        (None, "tus_pending_files"),
        ("test_folder", "test_folder"),
    ],
)
async def test_create_tus_upload_filesystem(rf, overwrite_base_path, result_base_path):
    user = await f.create_user()
    request = rf.get("/test")
    with patch(
        "commons.storage.repositories.process_new_tus_content", autospec=True
    ) as process_new_tus_content:
        await repositories.create_tus_upload(
            user=user,
            file_name="test.test",
            request=request,
            content_size=1 * KILOBYTE,
            total_size=1 * KILOBYTE,
            completion_hook="",
            completion_hook_parameters={},
            overwrite_base_path=overwrite_base_path,
        )
    process_new_tus_content.assert_awaited_once()
    tus_upload = await TusUpload.objects.aget()
    assert re.match(rf"^{result_base_path}/.+/test.test$", tus_upload.file.name)


@pytest.mark.parametrize(
    "overwrite_base_path, result_base_path",
    [
        (None, "tus_pending_files"),
        ("test_folder", "test_folder"),
    ],
)
@override_settings(**{"STORAGES": S3_STORAGE_SETTINGS})
async def test_create_tus_upload_s3(rf, overwrite_base_path, result_base_path):
    user = await f.create_user()
    request = rf.get("/test")
    file_field = TusUpload._meta.get_field("file")
    storage = file_field.storage
    with (
        patch(
            "commons.storage.repositories.process_new_tus_content", autospec=True
        ) as process_new_tus_content,
        patch.object(storage, "_open", autospec=True) as fake_storage_open,
        patch.object(
            storage,
            "get_available_name",
            autospec=True,
            side_effect=lambda name, max_length: name,
        ) as fake_get_available_name,
    ):
        fake_storage_open.return_value.obj.key = "test_key"
        fake_storage_open.return_value.obj.initiate_multipart_upload.return_value.id = (
            "test_id"
        )
        await repositories.create_tus_upload(
            user=user,
            file_name="test.test",
            request=request,
            content_size=1 * KILOBYTE,
            total_size=1 * KILOBYTE,
            completion_hook="",
            completion_hook_parameters={},
            overwrite_base_path=overwrite_base_path,
        )
    process_new_tus_content.assert_awaited_once()
    tus_upload = await TusUpload.objects.aget()
    tus_upload.pending_upload_data == S3PendingUploadData(
        upload_id="test_id", object_key="test_key"
    )
    file_name = fake_storage_open.call_args.args[0]
    assert re.match(rf"^{result_base_path}/.+/test.test$", file_name)


def test_delete_tus_upload_filesystem():
    tus_upload = f.TusUploadFactory.create()
    path = tus_upload.file.path
    assert Path(path).exists()

    with TestCase.captureOnCommitCallbacks(execute=True) as callbacks:
        assert repositories.delete_tus_upload(tus_upload)
    assert not Path(path).exists()


@override_settings(**{"STORAGES": S3_STORAGE_SETTINGS})
def test_delete_tus_upload_s3():
    file_field = TusUpload._meta.get_field("file")
    storage = file_field.storage
    s3 = boto3.resource("s3")
    mock_abort = Mock(
        spec=s3.MultipartUpload("", "", "").abort, side_effect=ClientError({}, "")
    )
    tus_upload = f.TusUploadFactory.create(
        file=None,
        pending_upload_data=S3PendingUploadData(
            upload_id="test_id", object_key="test_key"
        ),
    )

    with (
        TestCase.captureOnCommitCallbacks(execute=True) as callbacks,
        patch_s3_multipart_upload(mock_abort=mock_abort),
        patch.object(storage, "delete") as wrapped_delete,
    ):
        assert repositories.delete_tus_upload(tus_upload)
    mock_abort.assert_called_once()
    wrapped_delete.assert_called_once_with("test_key")


async def test_process_new_tus_content_overflow_size(rf):
    tus_upload = f.build_tus_upload(offset=1, total_size=1)
    request = rf.get("/test")
    with pytest.raises(ex.OverflowExpectedSizeError):
        await repositories.process_new_tus_content(tus_upload, request, 1)


async def test_process_new_tus_content_filesystem_overflow_content():
    tus_upload = await f.create_tus_upload(offset=1, total_size=6)
    request = BytesIO(b"a" * 6)
    with pytest.raises(ex.OverflowExpectedSizeError):
        await repositories.process_new_tus_content(tus_upload, request, 2)
    assert tus_upload.offset == 7


async def test_process_new_tus_content_filesystem():
    tus_upload = await f.create_tus_upload(offset=0, total_size=6)
    request = BytesIO(b"a" * 2)
    tus_upload = await repositories.process_new_tus_content(tus_upload, request, 2)
    assert tus_upload.offset == 2


async def test_process_new_tus_content_filesystem_interrupted():
    tus_upload = await f.create_tus_upload(offset=0, total_size=6)
    request = BytesIO(b"a" * 2)
    tus_upload = await repositories.process_new_tus_content(tus_upload, request, 2)
    assert tus_upload.offset == 2
    request = BytesIO(b"b" * 3)
    with patch(
        "commons.storage.repositories._check_stored_length",
        side_effect=ex.OverflowExpectedSizeError(),
    ), pytest.raises(ex.OverflowExpectedSizeError):
        tus_upload = await repositories.process_new_tus_content(tus_upload, request, 3)
    request = BytesIO(b"c" * 3)
    tus_upload = await repositories.process_new_tus_content(tus_upload, request, 3)
    with tus_upload.file.open("rb") as file:
        assert file.read(5) == b"aaccc"


async def test_process_new_tus_content_filesystem_last_write():
    tus_upload = await f.create_tus_upload(
        offset=4,
        total_size=6,
        completion_hook="itertools.repeat",
        completion_hook_parameters={"elem": 1},
    )
    request = BytesIO(b"a" * 2)
    with patch("itertools.repeat") as patched_completion_hook:
        tus_upload = await repositories.process_new_tus_content(tus_upload, request, 2)
    assert tus_upload.offset == 6
    assert not await TusUpload.objects.filter(id=tus_upload.id).aexists()
    patched_completion_hook.assert_called_once_with(elem=1, tus_upload=tus_upload)


@override_settings(**{"STORAGES": S3_STORAGE_SETTINGS})
async def test_process_new_tus_content_s3_overflow_content():
    tus_upload = await f.create_tus_upload(
        file=None,
        pending_upload_data=S3PendingUploadData(
            upload_id="test_id", object_key="test_key"
        ),
        offset=1,
        total_size=6,
    )
    request = BytesIO(b"a" * 6)
    with (
        pytest.raises(ex.OverflowExpectedSizeError),
        patch_s3_multipart_upload(),
    ):
        await repositories.process_new_tus_content(tus_upload, request, 2)
    assert tus_upload.offset == 7


@override_settings(**{"STORAGES": S3_STORAGE_SETTINGS})
async def test_process_new_tus_content_s3():
    tus_upload = await f.create_tus_upload(
        file=None,
        pending_upload_data=S3PendingUploadData(
            upload_id="test_id", object_key="test_key"
        ),
        offset=0,
        total_size=6,
    )
    request = BytesIO(b"a" * 2)
    with patch_s3_multipart_upload():
        tus_upload = await repositories.process_new_tus_content(tus_upload, request, 2)
    assert tus_upload.offset == 2


@override_settings(**{"STORAGES": S3_STORAGE_SETTINGS})
async def test_process_new_tus_content_s3_no_upload():
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

    tus_upload = await f.create_tus_upload(
        file=None,
        pending_upload_data=S3PendingUploadData(
            upload_id="test_id", object_key="test_key"
        ),
        offset=0,
        total_size=6,
    )
    request = BytesIO(b"a" * 2)
    with (
        patch_s3_multipart_upload(mock_parts=mock_parts),
        patch.object(storage, "delete") as wrapped_delete,
        pytest.raises(ex.NoOngoingMultipartUploadError),
    ):
        await repositories.process_new_tus_content(tus_upload, request, 2)
    assert tus_upload.id is None
    wrapped_delete.assert_called_once_with("test_key")


@override_settings(**{"STORAGES": S3_STORAGE_SETTINGS})
async def test_process_new_tus_content_s3_client_error():
    s3 = boto3.resource("s3")
    mock_upload = Mock(
        spec=s3.MultipartUploadPart("", "", "", 1).upload,
        side_effect=ClientError({}, ""),
    )
    file_field = TusUpload._meta.get_field("file")
    storage = file_field.storage

    tus_upload = await f.create_tus_upload(
        file=None,
        pending_upload_data=S3PendingUploadData(
            upload_id="test_id", object_key="test_key"
        ),
        offset=0,
        total_size=6,
    )
    request = BytesIO(b"a" * 2)
    with (
        pytest.raises(ClientError),
        patch_s3_multipart_upload(mock_upload=mock_upload) as multipart_mocks,
        patch.object(storage, "delete", autospec=True) as fake_storage_delete,
    ):
        await repositories.process_new_tus_content(tus_upload, request, 2)
    (mock_complete, mock_abort, mock_upload, mock_parts) = multipart_mocks
    mock_abort.assert_called_once()


@override_settings(**{"STORAGES": S3_STORAGE_SETTINGS})
async def test_process_new_tus_content_s3_last_write():
    tus_upload = await f.create_tus_upload(
        file=None,
        pending_upload_data=S3PendingUploadData(
            upload_id="test_id", object_key="test_key"
        ),
        offset=4,
        total_size=6,
        completion_hook="itertools.repeat",
        completion_hook_parameters={"elem": 1},
    )
    request = BytesIO(b"a" * 2)
    with (
        TestCase.captureOnCommitCallbacks(execute=True) as callbacks,
        patch("itertools.repeat") as patched_completion_hook,
        patch_s3_multipart_upload() as multipart_mocks,
    ):
        tus_upload = await repositories.process_new_tus_content(tus_upload, request, 2)
    (mock_complete, mock_abort, mock_upload, mock_parts) = multipart_mocks
    assert tus_upload.offset == 6
    assert tus_upload.file == "test_key"
    mock_complete.assert_called_once_with(
        MultipartUpload={"Parts": [S3Part(ETag="test-etag", PartNumber=1)]}
    )
    assert not await TusUpload.objects.filter(id=tus_upload.id).aexists()
    patched_completion_hook.assert_called_once_with(elem=1, tus_upload=tus_upload)
