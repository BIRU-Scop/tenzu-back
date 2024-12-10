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

from django.db import migrations, models

import base.db.models
import base.utils.datetime


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Story",
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
                    "title_updated_at",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="title updated at"
                    ),
                ),
                (
                    "description_updated_at",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="description updated at"
                    ),
                ),
                (
                    "version",
                    models.PositiveBigIntegerField(default=1, verbose_name="version"),
                ),
                (
                    "ref",
                    models.BigIntegerField(
                        db_index=True, default=0, verbose_name="ref"
                    ),
                ),
                ("title", models.CharField(max_length=500, verbose_name="title")),
                (
                    "description",
                    models.TextField(blank=True, null=True, verbose_name="description"),
                ),
                (
                    "order",
                    models.DecimalField(
                        decimal_places=10,
                        default=100,
                        max_digits=16,
                        verbose_name="order",
                    ),
                ),
            ],
            options={
                "verbose_name": "story",
                "verbose_name_plural": "stories",
                "ordering": ["project", "workflow", "order"],
            },
        ),
    ]
