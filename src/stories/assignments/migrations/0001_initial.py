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

import base.db.models
import base.utils.datetime


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("stories", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="StoryAssignment",
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
                    "story",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="story_assignments",
                        to="stories.story",
                        verbose_name="story",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="story_assignments",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="user",
                    ),
                ),
            ],
            options={
                "verbose_name": "story assignment",
                "verbose_name_plural": "story assignments",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="storyassignment",
            index=models.Index(fields=["story", "user"], name="stories_ass_story_i_bb03e4_idx"),
        ),
        migrations.AddConstraint(
            model_name="storyassignment",
            constraint=models.UniqueConstraint(
                fields=("story", "user"),
                name="stories_assignments_storyassignment_unique_story_user",
            ),
        ),
    ]
