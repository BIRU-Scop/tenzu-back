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

from typing import Annotated

from pydantic import Field

from commons.utils.colors import NUM_COLORS
from commons.validators import B64UUID, BaseValidatorSchema
from commons.validators.fields.text import Label


class StoryTagCreateValidator(BaseValidatorSchema):
    label: Label
    color: Annotated[int, Field(ge=1, le=NUM_COLORS)]


class StoryTagUpdateValidator(BaseValidatorSchema):
    label: Label
    color: Annotated[int, Field(ge=1, le=NUM_COLORS)]


class StoryTagAssignValidator(BaseValidatorSchema):
    tag_id: B64UUID
