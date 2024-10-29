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

from base.db import models
from base.db.mixins import CreatedMetaInfoMixin


class Attachment(models.BaseModel, CreatedMetaInfoMixin):
    storaged_object = models.ForeignKey(
        "storage.StoragedObject",
        null=False,
        blank=False,
        on_delete=models.RESTRICT,
        related_name="attachments",
        verbose_name="storaged object",
    )
    name = models.TextField(
        null=False,
        blank=False,
        verbose_name="file name",
    )
    content_type = models.TextField(
        null=False,
        blank=False,
        verbose_name="file content type",
    )
    size = models.IntegerField(
        null=False,
        blank=False,
        verbose_name="file size (bytes)",
    )

    object_content_type = models.ForeignKey(
        "contenttypes.ContentType",
        null=False,
        blank=False,
        on_delete=models.CASCADE,
        verbose_name="object content type",
    )
    object_id = models.UUIDField(null=False, blank=False, verbose_name="object id")
    # NOTE: the content_object should have a project attribute.
    content_object = models.GenericForeignKey(
        "object_content_type",
        "object_id",
    )

    class Meta:
        verbose_name = "attachment"
        verbose_name_plural = "attachments"
        indexes = [
            models.Index(fields=["object_content_type", "object_id"]),
        ]
        ordering = ["object_content_type", "object_id", "-created_at"]

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"<Attachment {self.name}>"
