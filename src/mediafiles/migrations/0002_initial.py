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
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("projects", "0001_initial"),
        ("mediafiles", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="mediafile",
            name="project",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="mediafiles",
                to="projects.project",
                verbose_name="project",
            ),
        ),
        migrations.AddIndex(
            model_name="mediafile",
            index=models.Index(
                fields=["object_content_type", "object_id"],
                name="mediafiles__object__cb24da_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="mediafile",
            index=models.Index(
                fields=["project"], name="mediafiles__project_e8bd81_idx"
            ),
        ),
    ]
