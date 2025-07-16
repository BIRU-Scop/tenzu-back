# -*- coding: utf-8 -*-
# Copyright (C) 2024-2025 BIRU
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
from enum import StrEnum

from pydantic import BaseModel, model_validator
from typing_extensions import Self


class StorageBackends(StrEnum):
    FileSystemStorage = "django.core.files.storage.FileSystemStorage"
    S3Storage = "storages.backends.s3.S3Storage"


class StaticStorageBackends(StrEnum):
    StaticFilesStorage = "django.contrib.staticfiles.storage.StaticFilesStorage"
    ManifestStaticFilesStorage = (
        "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"
    )
    CompressedManifestWhitenoiseStorage = (
        "whitenoise.storage.CompressedManifestStaticFilesStorage"
    )
    CompressedWhitenoiseStorage = "whitenoise.storage.CompressedStaticFilesStorage"


class StorageSettings(BaseModel):
    AWS_ACCESS_KEY_ID: str | None = None
    AWS_S3_SECRET_ACCESS_KEY: str | None = None
    AWS_STORAGE_BUCKET_NAME: str | None = None
    AWS_S3_ENDPOINT_URL: str | None = None
    AWS_S3_FILE_OVERWRITE: bool = False

    CLEAN_DELETED_STORAGE_OBJECTS_CRON: str = (
        "0 4 * * *"  # default: once a day, at 4:00 AM
    )
    DAYS_TO_STORE_DELETED_STORAGED_OBJECTS: int = 90  # 90 day
    BACKEND_CLASS: StorageBackends = StorageBackends.FileSystemStorage
    STATIC_BACKEND_CLASS: StaticStorageBackends = (
        StaticStorageBackends.CompressedManifestWhitenoiseStorage
    )

    @model_validator(mode="after")
    def validate_storage_backend(self) -> Self:
        if self.BACKEND_CLASS == StorageBackends.S3Storage:
            if self.AWS_ACCESS_KEY_ID is None:
                raise ValueError("AWS_ACCESS_KEY_ID is required")
            if self.AWS_S3_SECRET_ACCESS_KEY is None:
                raise ValueError("AWS_S3_SECRET_ACCESS_KEY is required")
            if self.AWS_STORAGE_BUCKET_NAME is None:
                raise ValueError("AWS_STORAGE_BUCKET_NAME is required")
            if self.AWS_S3_ENDPOINT_URL is None:
                raise ValueError("AWS_S3_ENDPOINT_URL is required")
        return self
