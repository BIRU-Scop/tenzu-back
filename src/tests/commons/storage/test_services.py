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
import binascii
from unittest.mock import patch

import pytest

from commons.storage import exceptions as ex
from commons.storage import services
from ninja_jwt.utils import aware_utcnow
from tests.utils import factories as f

##########################################################
# storaged object
########################################################


def test_clean_deleted_storaged_objects():
    with (
        patch(
            "commons.storage.services.storage_repositories", autospec=True
        ) as fake_storage_repositories,
    ):
        fake_storage_repositories.list_storaged_objects.return_value = [
            f.build_storaged_object()
        ] * 3
        fake_storage_repositories.delete_storaged_object.side_effect = [
            True,
            True,
            False,
        ]
        assert services.clean_deleted_storaged_objects(aware_utcnow()) == 2
    assert fake_storage_repositories.delete_storaged_object.call_count == 3


##########################################################
# tus upload
########################################################


async def test_create_tus_upload(rf):
    request = rf.get("/test")
    with (
        patch(
            "commons.storage.services.storage_repositories", autospec=True
        ) as fake_storage_repositories,
    ):
        await services.create_tus_upload(
            user=f.build_user(),
            file_name="",
            file_content_type="test",
            request=request,
            content_size=0,
            total_size=0,
            completion_hook="",
            completion_hook_parameters={},
        )
    assert request.content_type == "test"
    fake_storage_repositories.create_tus_upload.assert_awaited_once()


async def test_process_new_tus_content(rf):
    request = rf.get("/test")
    with (
        patch(
            "commons.storage.services.storage_repositories", autospec=True
        ) as fake_storage_repositories,
    ):
        with pytest.raises(ex.MisalignedOffsets):
            await services.process_new_tus_content(
                tus_upload=f.build_tus_upload(offset=1),
                upload_offset=2,
                request=request,
                content_size=0,
            )
        await services.process_new_tus_content(
            tus_upload=f.build_tus_upload(offset=1),
            upload_offset=1,
            request=request,
            content_size=0,
        )
    fake_storage_repositories.process_new_tus_content.assert_awaited_once()


def test_parse_tus_metadata():
    assert services.parse_tus_metadata("") == {}
    assert services.parse_tus_metadata("key1 dmFsdWUx,key2,key3 dmFsdWUz") == {
        "key1": "value1",
        "key2": None,
        "key3": "value3",
    }
    assert services.parse_tus_metadata("key2") == {"key2": None}
    assert services.parse_tus_metadata(
        "originType VEE=,filename Zm9vLmpzb24=,filetype YXBwbGljYXRpb24vanNvbg=="
    ) == {"originType": "TA", "filename": "foo.json", "filetype": "application/json"}
    with pytest.raises(binascii.Error):
        services.parse_tus_metadata("badFormat invalid")


def test_clean_expired_tus_uploads():
    with (
        patch(
            "commons.storage.services.storage_repositories", autospec=True
        ) as fake_storage_repositories,
    ):
        fake_storage_repositories.list_tus_uploads.return_value = [
            f.build_storaged_object()
        ] * 3
        fake_storage_repositories.delete_tus_upload.side_effect = [
            True,
            True,
            False,
        ]
        assert services.clean_expired_tus_uploads(aware_utcnow()) == 2
    assert fake_storage_repositories.delete_tus_upload.call_count == 3
