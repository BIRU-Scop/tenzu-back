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

import django.contrib.postgres.fields
import django.db.models.deletion
from django.db import migrations, models

import base.db.models
import base.db.models.fields
import base.utils.datetime


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("projects", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProjectRole",
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
                ("name", models.CharField(max_length=200, verbose_name="name")),
                (
                    "slug",
                    base.db.models.fields.LowerSlugField(blank=True, max_length=250, verbose_name="slug"),
                ),
                (
                    "permissions",
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
                        verbose_name="permissions",
                    ),
                ),
                (
                    "order",
                    models.BigIntegerField(default=base.utils.datetime.timestamp_mics, verbose_name="order"),
                ),
                (
                    "is_admin",
                    models.BooleanField(default=False, verbose_name="is_admin"),
                ),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="roles",
                        to="projects.project",
                        verbose_name="project",
                    ),
                ),
            ],
            options={
                "verbose_name": "project role",
                "verbose_name_plural": "project roles",
                "ordering": ["project", "order", "name"],
            },
        ),
        migrations.AddIndex(
            model_name="projectrole",
            index=models.Index(fields=["project", "slug"], name="projects_ro_project_63cac9_idx"),
        ),
        migrations.AddConstraint(
            model_name="projectrole",
            constraint=models.UniqueConstraint(
                fields=("project", "slug"),
                name="projects_roles_projectrole_unique_project_slug",
            ),
        ),
        migrations.AddConstraint(
            model_name="projectrole",
            constraint=models.UniqueConstraint(
                fields=("project", "name"),
                name="projects_roles_projectrole_unique_project_name",
            ),
        ),
    ]
