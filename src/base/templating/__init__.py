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

from jinja2 import Environment, PackageLoader, select_autoescape

from base import front
from base.templating import filters
from base.utils import datetime
from configurations.conf import settings


def get_environment() -> Environment:
    # TODO: FIX:
    #    This module is not generic. It has a heavy dependency on tenzu.emails because of the loader.
    #    It should be calculated which modules have templates to load them all.
    env = Environment(loader=PackageLoader("emails"), autoescape=select_autoescape())

    # Load global variables
    env.globals["settings"] = settings
    env.globals["resolve_front_url"] = front.resolve_front_url
    env.globals["display_lifetime"] = datetime.display_lifetime

    # Load common filters
    filters.load_filters(env)

    return env


env = get_environment()
