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

from datetime import datetime

from base.i18n import i18n
from base.i18n.formatings import datetime as formating_datetime


def test_using_current_lang_wrapper():
    dt = datetime.utcnow()
    fdt1 = fdt2 = fdt3 = ""

    with i18n.use("es-ES"):
        fdt1 = formating_datetime.format_datetime(dt)
    with i18n.use("en-US"):
        fdt2 = formating_datetime.format_datetime(dt)
    with i18n.use("es-ES"):
        fdt3 = formating_datetime.format_datetime(dt)

    assert fdt1 == fdt3 != fdt2
