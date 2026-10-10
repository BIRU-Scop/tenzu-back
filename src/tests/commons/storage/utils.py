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

from contextlib import contextmanager
from typing import Generator
from unittest.mock import MagicMock, Mock, patch

import boto3
from boto3.resources.factory import ResourceFactory
from django.conf import settings

from configurations.conf.storage import StorageBackends

S3_STORAGE_SETTINGS = {
    "default": {
        "BACKEND": StorageBackends.S3Storage.value,
    },
    "staticfiles": settings.STORAGES["staticfiles"],
}


@contextmanager
def patch_s3_multipart_upload(
    mock_complete=None, mock_abort=None, mock_upload=None, mock_parts=None
) -> Generator[tuple[Mock, Mock, Mock, Mock]]:
    s3 = boto3.resource("s3")
    real_create_action = ResourceFactory._create_action
    real_create_collection = ResourceFactory._create_collection

    if mock_complete is None:
        mock_complete = Mock(spec=s3.MultipartUpload("", "", "").complete)
    if mock_abort is None:
        mock_abort = Mock(spec=s3.MultipartUpload("", "", "").abort)
    if mock_upload is None:
        mock_upload = Mock(
            spec=s3.MultipartUploadPart("", "", "", 1).upload,
            return_value={"ETag": "test-etag"},
        )
    if mock_parts is None:
        mock_parts = MagicMock(spec=s3.MultipartUpload("", "", "").parts)

    def mock_multipart_create_action(
        factory_self,
        action_model,
        resource_name,
        service_context,
        is_load=False,
    ):
        if resource_name == "MultipartUpload":
            if action_model.name == "complete":
                return mock_complete
            if action_model.name == "abort":
                return mock_abort
        if resource_name == "MultipartUploadPart" and action_model.name == "upload":
            return mock_upload
        return real_create_action(
            factory_self, action_model, resource_name, service_context, is_load
        )

    def mock_multipart_create_collection(
        factory_self, resource_name, collection_model, service_context
    ):
        if resource_name == "MultipartUpload" and collection_model.name == "parts":
            return mock_parts
        return real_create_collection(
            factory_self, resource_name, collection_model, service_context
        )

    with (
        patch.object(
            ResourceFactory, "_create_action", new=mock_multipart_create_action
        ),
        patch.object(
            ResourceFactory, "_create_collection", new=mock_multipart_create_collection
        ),
    ):
        yield (mock_complete, mock_abort, mock_upload, mock_parts)
