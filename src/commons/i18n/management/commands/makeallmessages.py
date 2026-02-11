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
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import translation

from commons import i18n


class Command(BaseCommand):
    help = "call makemessages for all available languages"

    def handle(self, *args, **options):
        call_command(
            "makemessages",
            locale=[translation.to_locale(loc.code) for loc in i18n.get_locales()],
        )
