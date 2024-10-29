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


class Migration(migrations.Migration):
    dependencies = [
        (
            "workflows",
            "0003_remove_workflowstatus_workflows_workflowstatus_unique_workflow_slug_and_more",
        ),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="workflow",
            name="workflows_workflow_unique_project_name",
        ),
        migrations.AlterField(
            model_name="workflow",
            name="order",
            field=models.DecimalField(decimal_places=10, default=100, max_digits=16, verbose_name="order"),
        ),
    ]
