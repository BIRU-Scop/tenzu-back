# -*- coding: utf-8 -*-
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

import unicodedata
from typing import Annotated

from pydantic import AfterValidator, Field, StringConstraints

from commons.colors import NUM_COLORS
from commons.validators import B64UUID, BaseValidatorSchema


def _check_no_control_characters(value: str) -> str:
    if any(unicodedata.category(char) in ("Cc", "Cf") for char in value):
        raise ValueError("Control characters are not allowed")
    return value


def _normalize_nfc(value: str) -> str:
    return unicodedata.normalize("NFC", value)


Label = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=50),
    AfterValidator(_check_no_control_characters),
    AfterValidator(_normalize_nfc),
]


class StoryTagCreateValidator(BaseValidatorSchema):
    label: Label
    color: Annotated[int, Field(ge=1, le=NUM_COLORS)]


class StoryTagUpdateValidator(BaseValidatorSchema):
    label: Label
    color: Annotated[int, Field(ge=1, le=NUM_COLORS)]


class StoryTagAssignValidator(BaseValidatorSchema):
    tag_id: B64UUID
