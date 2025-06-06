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

from os import path

from django.contrib.contenttypes.fields import GenericForeignKey
from django.db import models

from base.db.models import BaseModel
from base.db.models.mixins import CreatedMetaInfoMixin
from base.utils.files import get_obfuscated_file_path


def get_mediafile_file_path(instance: "Mediafile", filename: str) -> str:
    label = instance.project._meta.app_label
    model_name = (
        instance.project._meta.model_name or instance.project.__class__.__name__
    )

    base_path = path.join(
        "mediafiles",
        f"{label.lower()}_{model_name.lower()}",
        instance.project.b64id,
    )
    return get_obfuscated_file_path(instance, filename, base_path)


class Mediafile(BaseModel, CreatedMetaInfoMixin):
    # TODO: We need to remove file on delete project and content_object. It may depend on the real life that
    #       the files have beyond their content object (especially with history or activity timelines).
    #       (Some inspiration https://github.com/un1t/django-cleanup)
    file = models.FileField(
        upload_to=get_mediafile_file_path,
        max_length=500,
        null=False,
        blank=False,
        verbose_name="file",
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
    project = models.ForeignKey(
        "projects.Project",
        null=False,
        blank=False,
        related_name="mediafiles",
        on_delete=models.CASCADE,
        verbose_name="project",
    )

    object_content_type = models.ForeignKey(
        "contenttypes.ContentType",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        verbose_name="object content type",
    )
    object_id = models.UUIDField(null=True, blank=True, verbose_name="object id")
    content_object = GenericForeignKey(
        "object_content_type",
        "object_id",
    )

    class Meta:
        verbose_name = "mediafile"
        verbose_name_plural = "mediafiles"
        indexes = [
            models.Index(fields=["object_content_type", "object_id"]),
            models.Index(fields=["project"]),
        ]

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"<Mediafile {self.name}>"
