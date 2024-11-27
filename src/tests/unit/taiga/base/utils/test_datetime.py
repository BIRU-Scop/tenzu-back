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
from datetime import timedelta

from base.i18n import i18n
from base.utils.datetime import display_lifetime


def test_display_lifetime():
    with i18n.use("en-US"):
        assert display_lifetime(timedelta(days=3)) == "3 days"

        assert display_lifetime(timedelta(days=1, hours=12)) == "1 day"

        assert display_lifetime(timedelta(days=1)) == "1 day"

        assert display_lifetime(timedelta(hours=12)) == "12 hours"

        assert display_lifetime(timedelta(hours=3, minutes=30)) == "3 hours"

        assert display_lifetime(timedelta(hours=1)) == "1 hour"

        assert display_lifetime(timedelta(minutes=45)) == "45 minutes"

        assert display_lifetime(timedelta(minutes=1)) == "1 minute"

        assert display_lifetime(timedelta(minutes=0)) == "0 minutes"
