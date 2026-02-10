# Copyright (C) 2024-2026 BIRU
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
from django.conf import settings
from django.core.management.base import BaseCommand
from rich.console import Console
from rich.table import Table

from base.i18n import (
    i18n,
)


class Command(BaseCommand):
    help = "List available languages"

    def handle(self, *args, **options):
        table = Table(title="Available languages")
        table.add_column("Code", style="bold yellow")
        table.add_column("Name (EN)")
        table.add_column("Language")
        table.add_column("Territory")
        table.add_column("Extra", style="italic")

        for loc in i18n.locales:
            code = i18n.get_locale_code(loc)
            name = loc.english_name
            language = loc.language_name
            territory = loc.territory_name
            extra: list[str] = []
            if code == settings.LANGUAGE_CODE:
                extra.append("default")

            table.add_row(code, name, language, territory, ", ".join(extra))

        console = Console()
        console.print(table)
