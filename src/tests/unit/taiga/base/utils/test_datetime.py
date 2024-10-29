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

from base.i18n import i18n
from base.utils.datetime import display_lifetime


def test_display_lifetime():
    with i18n.use("en-US"):
        minutes = 3 * 24 * 60  # 3 days
        assert display_lifetime(minutes) == "3 days"

        minutes = 36 * 60  # 1,5 days
        assert display_lifetime(minutes) == "1 day"

        minutes = 24 * 60  # 1 day
        assert display_lifetime(minutes) == "1 day"

        minutes = 12 * 60  # 12 hours
        assert display_lifetime(minutes) == "12 hours"

        minutes = 210  # 3,5 hours
        assert display_lifetime(minutes) == "3 hours"

        minutes = 60  # 1 hour
        assert display_lifetime(minutes) == "1 hour"

        minutes = 45  # 45 minutes
        assert display_lifetime(minutes) == "45 minutes"

        minutes = 1  # 1 minute
        assert display_lifetime(minutes) == "1 minute"

        minutes = 0  # 0 minutes
        assert display_lifetime(minutes) == "0 minutes"

        minutes = -1  # -1 minutes
        assert display_lifetime(minutes) == "-1 minutes"
