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
        ("workflows", "0002_alter_workflow_slug_alter_workflowstatus_name_and_more"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="workflowstatus",
            name="workflows_workflowstatus_unique_workflow_slug",
        ),
        migrations.RemoveIndex(
            model_name="workflowstatus",
            name="workflows_w_workflo_b8ac5c_idx",
        ),
        migrations.RemoveField(
            model_name="workflowstatus",
            name="slug",
        ),
        migrations.AddIndex(
            model_name="workflowstatus",
            index=models.Index(
                fields=["workflow", "id"], name="workflows_w_workflo_83740e_idx"
            ),
        ),
        migrations.AddConstraint(
            model_name="workflowstatus",
            constraint=models.UniqueConstraint(
                fields=("workflow", "id"),
                name="workflows_workflowstatus_unique_workflow_id",
            ),
        ),
    ]
