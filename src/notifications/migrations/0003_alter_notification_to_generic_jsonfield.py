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

# Generated by Django 5.1.3 on 2024-12-02 13:15

from django.conf import settings
from django.db import migrations, models

import base.utils.json


class Migration(migrations.Migration):
    dependencies = [
        ("notifications", "0002_alter_notification_content"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name="notification",
            name="content",
            field=models.JSONField(
                default=dict,
                encoder=base.utils.json.JSONEncoder,
                verbose_name="content",
            ),
        ),
    ]
