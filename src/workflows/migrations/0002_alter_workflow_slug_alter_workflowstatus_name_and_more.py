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

import base.db.models.fields


class Migration(migrations.Migration):
    dependencies = [
        ("workflows", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="workflow",
            name="slug",
            field=base.db.models.fields.LowerSlugField(max_length=250, verbose_name="slug"),
        ),
        migrations.AlterField(
            model_name="workflowstatus",
            name="name",
            field=models.CharField(max_length=30, verbose_name="name"),
        ),
        migrations.AlterField(
            model_name="workflowstatus",
            name="order",
            field=models.DecimalField(decimal_places=10, default=100, max_digits=16, verbose_name="order"),
        ),
        migrations.AlterField(
            model_name="workflowstatus",
            name="slug",
            field=base.db.models.fields.LowerSlugField(max_length=250, verbose_name="slug"),
        ),
        migrations.AddConstraint(
            model_name="workflowstatus",
            constraint=models.UniqueConstraint(
                fields=("workflow", "slug"),
                name="workflows_workflowstatus_unique_workflow_slug",
            ),
        ),
    ]
