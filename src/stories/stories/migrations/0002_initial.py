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

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("stories", "0001_initial"),
        ("workflows", "0001_initial"),
        ("stories_assignments", "0001_initial"),
        ("projects", "0002_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="story",
            name="assignees",
            field=models.ManyToManyField(
                related_name="stories",
                through="stories_assignments.StoryAssignment",
                to=settings.AUTH_USER_MODEL,
                verbose_name="assignees",
            ),
        ),
        migrations.AddField(
            model_name="story",
            name="created_by",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.SET_NULL,
                to=settings.AUTH_USER_MODEL,
                verbose_name="created by",
            ),
        ),
        migrations.AddField(
            model_name="story",
            name="description_updated_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="%(app_label)s_%(class)s_description_updated_by",
                to=settings.AUTH_USER_MODEL,
                verbose_name="description updated by",
            ),
        ),
        migrations.AddField(
            model_name="story",
            name="project",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="stories",
                to="projects.project",
                verbose_name="project",
            ),
        ),
        migrations.AddField(
            model_name="story",
            name="status",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="stories",
                to="workflows.workflowstatus",
                verbose_name="status",
            ),
        ),
        migrations.AddField(
            model_name="story",
            name="title_updated_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="%(app_label)s_%(class)s_title_updated_by",
                to=settings.AUTH_USER_MODEL,
                verbose_name="title updated by",
            ),
        ),
        migrations.AddField(
            model_name="story",
            name="workflow",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="stories",
                to="workflows.workflow",
                verbose_name="workflow",
            ),
        ),
        migrations.AddIndex(
            model_name="story",
            index=models.Index(
                fields=["project", "ref"], name="stories_sto_project_840ba5_idx"
            ),
        ),
        migrations.AddConstraint(
            model_name="story",
            constraint=models.UniqueConstraint(
                fields=("project", "ref"), name="projects_unique_refs"
            ),
        ),
    ]
