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

import pytest
from pydantic import ValidationError

from base.validators import BaseModel
from base.validators.fields.text import StrNotEmpty

#########################################################
# StrNotEmpty
#########################################################


class Model(BaseModel):
    x: StrNotEmpty


def test_str_not_empty_with_valid_value():
    assert Model(x="a").x == "a"


@pytest.mark.parametrize(
    "value",
    ["", "   ", None],
)
def test_str_not_empty_with_invalid_value(value):
    with pytest.raises(ValidationError):
        Model(x=value)
