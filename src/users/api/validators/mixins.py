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

import string
from collections import Counter

from pydantic import StringConstraints, field_validator
from typing_extensions import Annotated

from base.validators import BaseModel


class PasswordMixin(BaseModel):
    password: Annotated[str, StringConstraints(min_length=8, max_length=256)]  # type: ignore

    @field_validator("password")
    @classmethod
    def check_password(cls, v: str) -> str:
        has_upper = len(set(string.ascii_uppercase).intersection(v)) > 0
        has_lower = len(set(string.ascii_lowercase).intersection(v)) > 0
        has_number = len(set(string.digits).intersection(v)) > 0
        has_symbol = len(set(string.punctuation).intersection(v)) > 0

        c = Counter([has_upper, has_lower, has_number, has_symbol])
        assert c[True] >= 3, "Invalid password"
        return v
