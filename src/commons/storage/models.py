# -*- coding: utf-8 -*-
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
import functools
from typing import TypedDict

from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models.functions import TruncDate

from base.db.models import BaseDBModel
from base.db.models.mixins import (
    CreatedAtMetaInfoMixin,
    CreatedMetaInfoMixin,
    DeletedAtMetaInfoMixin,
    ModifiedAtMetaInfoMixin,
)
from base.utils.files import get_obfuscated_file_path


def get_storaged_object_file_patch(instance: "StoragedObject", filename: str) -> str:
    return get_obfuscated_file_path(instance, filename, "storagedobjets")


class StoragedObject(BaseDBModel, CreatedAtMetaInfoMixin, DeletedAtMetaInfoMixin):
    file = models.FileField(
        upload_to=get_storaged_object_file_patch,
        max_length=500,
        null=False,
        blank=False,
        verbose_name="file",
    )

    class Meta:
        verbose_name = "storaged_object"
        verbose_name_plural = "storaged_objects"
        indexes = [
            models.Index(
                TruncDate("created_at"),
                "created_at",
                name="%(app_label)s_%(class)s_created",
            ),
            models.Index(
                TruncDate("deleted_at"),
                "deleted_at",
                name="%(app_label)s_%(class)s_deleted",
            ),
        ]
        ordering = [
            "-created_at",
        ]

    def __str__(self) -> str:
        return self.file.name

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.file.name}>"


get_tus_file_path = functools.partial(
    get_obfuscated_file_path, base_path="tus_pending_files"
)


class S3Part(TypedDict, total=True):
    ETag: str
    PartNumber: int


class S3PendingUploadData(TypedDict, total=True):
    upload_id: str
    object_key: str


class TusUpload(BaseDBModel, CreatedMetaInfoMixin, ModifiedAtMetaInfoMixin):
    file = models.FileField(
        upload_to=get_tus_file_path,
        max_length=500,
        null=True,
        blank=False,
        verbose_name="file",
    )
    offset = models.PositiveBigIntegerField(default=0)
    total_size = models.PositiveBigIntegerField()

    completion_hook = models.CharField(null=False, blank=False, max_length=128)
    completion_hook_parameters = models.JSONField(
        null=False, blank=True, default=dict, encoder=DjangoJSONEncoder
    )

    pending_upload_data: S3PendingUploadData | {} = models.JSONField(
        null=False,
        blank=True,
        default=dict,
        encoder=DjangoJSONEncoder,
        help_text="metadata that we need with s3 to handle multipart files",
    )

    class Meta:
        verbose_name = "tus_upload"
        verbose_name_plural = "tus_uploads"
        indexes = [
            models.Index(
                TruncDate("created_at"),
                "created_at",
                name="%(app_label)s_%(class)s_created",
            ),
        ]

    def __str__(self) -> str:
        return self.file.name

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.file.name}>"
