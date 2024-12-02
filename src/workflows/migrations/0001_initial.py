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

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models

import base.db.models
import base.utils.datetime


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("projects", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Workflow",
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
                ("name", models.CharField(max_length=250, verbose_name="name")),
                ("slug", models.CharField(max_length=250, verbose_name="slug")),
                (
                    "order",
                    models.BigIntegerField(
                        default=base.utils.datetime.timestamp_mics, verbose_name="order"
                    ),
                ),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="workflows",
                        to="projects.project",
                        verbose_name="project",
                    ),
                ),
            ],
            options={
                "verbose_name": "workflow",
                "verbose_name_plural": "workflows",
                "ordering": ["project", "order", "name"],
            },
        ),
        migrations.CreateModel(
            name="WorkflowStatus",
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
                ("name", models.CharField(max_length=250, verbose_name="name")),
                ("slug", models.CharField(max_length=250, verbose_name="slug")),
                (
                    "color",
                    models.IntegerField(
                        default=1,
                        validators=[django.core.validators.MaxValueValidator(8)],
                        verbose_name="color",
                    ),
                ),
                (
                    "order",
                    models.BigIntegerField(
                        default=base.utils.datetime.timestamp_mics, verbose_name="order"
                    ),
                ),
                (
                    "workflow",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="statuses",
                        to="workflows.workflow",
                        verbose_name="workflow",
                    ),
                ),
            ],
            options={
                "verbose_name": "workflow status",
                "verbose_name_plural": "workflow statuses",
                "ordering": ["workflow", "order", "name"],
            },
        ),
        migrations.AddIndex(
            model_name="workflowstatus",
            index=models.Index(
                fields=["workflow", "slug"], name="workflows_w_workflo_b8ac5c_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="workflow",
            index=models.Index(
                fields=["project", "slug"], name="workflows_w_project_5a96f0_idx"
            ),
        ),
        migrations.AddConstraint(
            model_name="workflow",
            constraint=models.UniqueConstraint(
                fields=("project", "slug"),
                name="workflows_workflow_unique_project_slug",
            ),
        ),
        migrations.AddConstraint(
            model_name="workflow",
            constraint=models.UniqueConstraint(
                fields=("project", "name"),
                name="workflows_workflow_unique_project_name",
            ),
        ),
    ]
