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
from base.db.mixins import (
    CreatedMetaInfoMixin,
    DeletedMetaInfoMixin,
    ModifiedAtMetaInfoMixin,
)
from projects.projects.models import Project


class Comment(
    models.BaseModel,
    CreatedMetaInfoMixin,
    ModifiedAtMetaInfoMixin,
    DeletedMetaInfoMixin,
):
    text = models.TextField(null=False, blank=False, verbose_name="text")
    object_content_type = models.ForeignKey(
        "contenttypes.ContentType",
        null=False,
        blank=False,
        on_delete=models.CASCADE,
        verbose_name="object content type",
    )
    object_id = models.UUIDField(null=False, blank=False, verbose_name="object id")
    content_object = models.GenericForeignKey(
        "object_content_type",
        "object_id",
    )

    class Meta:
        verbose_name = "comment"
        verbose_name_plural = "comments"
        indexes = [
            models.Index(fields=["object_content_type", "object_id"]),
        ]
        ordering = ["object_content_type", "object_id", "-created_at"]

    def __str__(self) -> str:
        return f'"{self.text}" (by {self.created_by} on {self.content_object})'

    def __repr__(self) -> str:
        return f"<Comment {self.id} [{self.content_object}]>"

    @property
    def project(self) -> Project:
        return getattr(self.content_object, "project")
