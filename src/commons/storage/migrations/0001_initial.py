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

import django.db.models.functions.datetime
from django.db import migrations, models

import base.db.models
import base.utils.datetime
import commons.storage.models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="StoragedObject",
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
                        default=base.utils.datetime.aware_utcnow,
                        verbose_name="created at",
                    ),
                ),
                (
                    "deleted_at",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="deleted at"
                    ),
                ),
                (
                    "file",
                    models.FileField(
                        max_length=500,
                        upload_to=commons.storage.models.get_storaged_object_file_patch,
                        verbose_name="file",
                    ),
                ),
            ],
            options={
                "verbose_name": "storaged_objects",
                "verbose_name_plural": "storaged_objects",
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(
                        django.db.models.functions.datetime.TruncDate("created_at"),
                        models.F("created_at"),
                        name="created_at_date_idx",
                    ),
                    models.Index(
                        django.db.models.functions.datetime.TruncDate("deleted_at"),
                        models.F("deleted_at"),
                        name="deleted_at_date_idx",
                    ),
                ],
            },
        ),
    ]
