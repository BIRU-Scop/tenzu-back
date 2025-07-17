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
import ninja_jwt.utils


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("storage", "0001_initial"),
        ("contenttypes", "0002_remove_content_type_name"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Attachment",
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
                ("name", models.TextField(verbose_name="file name")),
                ("content_type", models.TextField(verbose_name="file content type")),
                ("size", models.IntegerField(verbose_name="file size (bytes)")),
                ("object_id", models.UUIDField(verbose_name="object id")),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(app_label)s_%(class)s_created_by",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="created by",
                    ),
                ),
                (
                    "storaged_object",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.RESTRICT,
                        related_name="attachments",
                        to="storage.storagedobject",
                        verbose_name="storaged object",
                    ),
                ),
                (
                    "object_content_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="contenttypes.contenttype",
                        verbose_name="object content type",
                    ),
                ),
            ],
            options={
                "verbose_name": "attachment",
                "verbose_name_plural": "attachments",
                "ordering": ["object_content_type", "object_id", "-created_at"],
                "indexes": [
                    models.Index(
                        fields=["object_content_type", "object_id"],
                        name="attachments_object__8a3a6a_idx",
                    )
                ],
            },
        ),
    ]
