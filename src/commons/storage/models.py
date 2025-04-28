# -*- coding: utf-8 -*-
# Copyright (C) 2024 BIRU
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

from django.db import models
from django.db.models.functions import TruncDate

from base.db.models import BaseModel
from base.db.models.mixins import CreatedAtMetaInfoMixin, DeletedAtMetaInfoMixin
from base.utils.files import get_obfuscated_file_path


def get_storaged_object_file_patch(instance: "StoragedObject", filename: str) -> str:
    return get_obfuscated_file_path(instance, filename, "storagedobjets")


class StoragedObject(BaseModel, CreatedAtMetaInfoMixin, DeletedAtMetaInfoMixin):
    file = models.FileField(
        upload_to=get_storaged_object_file_patch,
        max_length=500,
        null=False,
        blank=False,
        verbose_name="file",
    )

    class Meta:
        verbose_name = "storaged_objects"
        verbose_name_plural = "storaged_objects"
        indexes = [
            models.Index(
                TruncDate("created_at"), "created_at", name="created_at_date_idx"
            ),
            models.Index(
                TruncDate("deleted_at"), "deleted_at", name="deleted_at_date_idx"
            ),
        ]
        ordering = [
            "-created_at",
        ]

    def __str__(self) -> str:
        return self.file.name

    def __repr__(self) -> str:
        return f"<StoragedObject {self.file.name}>"
