# Copyright (C) 2026 BIRU
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

from commons.utils.strings import get_unique_string_with_max_length


def test_get_unique_string_with_max_length():
    assert get_unique_string_with_max_length("test", 2, set()) == "te"
    assert get_unique_string_with_max_length("test", 2, {"te"}) == "t1"
    assert get_unique_string_with_max_length("test", 2, {"te", "t1"}) == "t2"
    assert (
        get_unique_string_with_max_length(
            "testestestestestest", 10, {"testestest"}, "foo"
        )
        == "footestes1"
    )
