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

import django.contrib.postgres.fields
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import base.db.models
import base.db.models.fields
import base.utils.datetime
import ninja_jwt.utils


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("projects", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProjectMembership",
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
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="memberships",
                        to="projects.project",
                        verbose_name="project",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="project_memberships",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="user",
                    ),
                ),
            ],
            options={
                "verbose_name": "project membership",
                "verbose_name_plural": "project memberships",
                "ordering": ["project", "user"],
            },
        ),
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
                    base.db.models.fields.LowerSlugField(
                        blank=True, max_length=250, verbose_name="slug"
                    ),
                ),
                (
                    "order",
                    models.BigIntegerField(
                        default=base.utils.datetime.timestamp_mics, verbose_name="order"
                    ),
                ),
                (
                    "is_owner",
                    models.BooleanField(default=False, verbose_name="is_owner"),
                ),
                (
                    "editable",
                    models.BooleanField(default=True, verbose_name="editable"),
                ),
                (
                    "permissions",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.CharField(
                            choices=[
                                (
                                    "create_modify_delete_role",
                                    "Create, modify or delete any editable role",
                                ),
                                ("modify_project", "Modify info of project"),
                                ("delete_project", "Delete the project"),
                                ("view_story", "View stories in project"),
                                ("modify_story", "Modify the stories"),
                                ("create_story", "Create new stories"),
                                ("delete_story", "Delete existing stories"),
                                ("view_comment", "View comments in stories"),
                                (
                                    "create_modify_delete_comment",
                                    "Post comment on stories, edit and delete own comments",
                                ),
                                ("moderate_comment", "Moderates other's comments"),
                                ("view_workflow", "View workflows in project"),
                                ("modify_workflow", "Modify the workflows"),
                                ("create_workflow", "Create new workflows"),
                                ("delete_workflow", "Delete existing workflows"),
                                ("create_modify_member", "Create or modify a member"),
                                ("delete_member", "Delete a member"),
                            ],
                            max_length=40,
                        ),
                        default=list,
                        size=None,
                        verbose_name="permissions",
                    ),
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
                (
                    "users",
                    models.ManyToManyField(
                        related_name="project_roles",
                        through="projects_memberships.ProjectMembership",
                        through_fields=("role", "user"),
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="users",
                    ),
                ),
            ],
            options={
                "verbose_name": "project role",
                "verbose_name_plural": "project roles",
                "ordering": ["project", "order", "name"],
            },
        ),
        migrations.AddField(
            model_name="projectmembership",
            name="role",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="memberships",
                to="projects_memberships.projectrole",
                verbose_name="role",
            ),
        ),
        migrations.AddIndex(
            model_name="projectrole",
            index=models.Index(
                fields=["project", "slug"], name="projects_me_project_fbe19a_idx"
            ),
        ),
        migrations.AddConstraint(
            model_name="projectrole",
            constraint=models.UniqueConstraint(
                fields=("project", "slug"),
                name="projects_memberships_projectrole_unique_project_slug",
            ),
        ),
        migrations.AddConstraint(
            model_name="projectrole",
            constraint=models.UniqueConstraint(
                fields=("project", "name"),
                name="projects_memberships_projectrole_unique_project_name",
            ),
        ),
        migrations.AddIndex(
            model_name="projectmembership",
            index=models.Index(
                fields=["project", "user"], name="projects_me_project_3bd46e_idx"
            ),
        ),
        migrations.AddConstraint(
            model_name="projectmembership",
            constraint=models.UniqueConstraint(
                fields=("project", "user"),
                name="projects_memberships_projectmembership_unique_project_user",
            ),
        ),
    ]
