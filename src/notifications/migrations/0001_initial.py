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


import django.contrib.postgres.fields.jsonb
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import base.db.models
import base.utils.datetime


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Notification",
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
                ("type", models.CharField(max_length=500, verbose_name="type")),
                (
                    "read_at",
                    models.DateTimeField(blank=True, null=True, verbose_name="read at"),
                ),
                (
                    "content",
                    django.contrib.postgres.fields.jsonb.JSONField(default=dict, verbose_name="content"),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="created by",
                    ),
                ),
                (
                    "owner",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="notifications",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="owner",
                    ),
                ),
            ],
            options={
                "verbose_name": "notification",
                "verbose_name_plural": "notifications",
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(fields=["owner"], name="notificatio_owner_i_2bc47d_idx"),
                    models.Index(
                        fields=["owner", "read_at"],
                        name="notificatio_owner_i_37308f_idx",
                    ),
                ],
            },
        ),
    ]
