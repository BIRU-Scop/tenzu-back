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

"""
This module contains elements to improve text formatting in the terminal. It is based on the rich library, see
https://rich.readthedocs.io/en/latest/ for more info
"""

from rich import print  # noqa
from rich.console import Console  # noqa
from rich.pretty import pprint  # noqa
from rich.syntax import Syntax  # noqa
from rich.table import Table  # noqa
