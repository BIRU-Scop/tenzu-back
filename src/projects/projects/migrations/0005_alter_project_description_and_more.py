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
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("projects", "0004_remove_projecttemplate_created_at_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="project",
            name="description",
            field=models.CharField(blank=True, default="", max_length=220, verbose_name="description"),
        ),
        migrations.AlterField(
            model_name="project",
            name="public_permissions",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.TextField(
                    choices=[
                        ("add_story", "Add story"),
                        ("comment_story", "Comment story"),
                        ("delete_story", "Delete story"),
                        ("modify_story", "Modify story"),
                        ("view_story", "View story"),
                    ]
                ),
                default=list,
                size=None,
                verbose_name="public permissions",
            ),
        ),
    ]
