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
from django.contrib.postgres.operations import CreateExtension
from django.db import migrations


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        CreateExtension("unaccent"),
        migrations.RunSQL(
            """
            DROP TEXT SEARCH CONFIGURATION IF EXISTS simple_unaccent cascade;
            CREATE TEXT SEARCH CONFIGURATION simple_unaccent ( COPY = pg_catalog.simple );
            ALTER TEXT SEARCH CONFIGURATION simple_unaccent
            ALTER MAPPING FOR hword, hword_part, word WITH unaccent, simple;
            """
        ),
    ]
