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

import functools

import django.contrib.postgres.fields
import django.contrib.postgres.fields.jsonb
import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import base.db.models
import base.db.models.fields
import base.utils.files
import ninja_jwt.utils


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Project",
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
                    "modified_at",
                    models.DateTimeField(auto_now=True, verbose_name="modified at"),
                ),
                ("name", models.CharField(max_length=80, verbose_name="name")),
                (
                    "description",
                    models.CharField(
                        blank=True,
                        max_length=220,
                        null=True,
                        verbose_name="description",
                    ),
                ),
                (
                    "color",
                    models.IntegerField(
                        blank=True,
                        default=1,
                        validators=[django.core.validators.MaxValueValidator(8)],
                        verbose_name="color",
                    ),
                ),
                (
                    "logo",
                    models.FileField(
                        blank=True,
                        max_length=500,
                        null=True,
                        upload_to=functools.partial(
                            base.utils.files.get_obfuscated_file_path,
                            *(),
                            **{"base_path": "project"},
                        ),
                        verbose_name="logo",
                    ),
                ),
                (
                    "public_permissions",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.TextField(
                            choices=[
                                ("add_story", "Add story"),
                                ("comment_story", "Comment story"),
                                ("delete_story", "Delete story"),
                                ("modify_story", "Modify story"),
                                ("view_story", "View story"),
                            ]
                        ),
                        blank=True,
                        default=list,
                        null=True,
                        size=None,
                        verbose_name="public permissions",
                    ),
                ),
            ],
            options={
                "verbose_name": "project",
                "verbose_name_plural": "projects",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="ProjectTemplate",
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
                    "modified_at",
                    models.DateTimeField(auto_now=True, verbose_name="modified at"),
                ),
                ("name", models.CharField(max_length=250, verbose_name="name")),
                (
                    "slug",
                    base.db.models.fields.LowerSlugField(
                        blank=True, max_length=250, unique=True, verbose_name="slug"
                    ),
                ),
                (
                    "roles",
                    django.contrib.postgres.fields.jsonb.JSONField(
                        blank=True, null=True, verbose_name="roles"
                    ),
                ),
                (
                    "workflows",
                    django.contrib.postgres.fields.jsonb.JSONField(
                        blank=True, null=True, verbose_name="workflows"
                    ),
                ),
            ],
            options={
                "verbose_name": "project template",
                "verbose_name_plural": "project templates",
                "ordering": ["name"],
            },
        ),
        migrations.AddIndex(
            model_name="projecttemplate",
            index=models.Index(fields=["slug"], name="projects_pr_slug_28d8d6_idx"),
        ),
        migrations.AddField(
            model_name="project",
            name="created_by",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.SET_NULL,
                to=settings.AUTH_USER_MODEL,
                verbose_name="created by",
            ),
        ),
    ]
