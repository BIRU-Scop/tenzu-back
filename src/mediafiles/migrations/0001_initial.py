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

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import base.db.models
import mediafiles.models
import ninja_jwt.utils


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        migrations.CreateModel(
            name="Mediafile",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        blank=True,
                        default=base.db.models.uuid_generator,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        default=ninja_jwt.utils.aware_utcnow,
                        verbose_name="created at",
                    ),
                ),
                (
                    "file",
                    models.FileField(
                        max_length=500,
                        upload_to=mediafiles.models.get_mediafile_file_path,
                        verbose_name="file",
                    ),
                ),
                ("name", models.TextField(verbose_name="file name")),
                ("content_type", models.TextField(verbose_name="file content type")),
                ("size", models.IntegerField(verbose_name="file size (bytes)")),
                (
                    "object_id",
                    models.UUIDField(blank=True, null=True, verbose_name="object id"),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="created by",
                    ),
                ),
                (
                    "object_content_type",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="contenttypes.contenttype",
                        verbose_name="object content type",
                    ),
                ),
            ],
            options={
                "verbose_name": "mediafile",
                "verbose_name_plural": "mediafiles",
            },
        ),
    ]
