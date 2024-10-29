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

from decimal import Decimal

from pydantic import ConfigDict, Field, field_validator
from pydantic_core.core_schema import ValidationInfo

from base.serializers import UUIDB64, BaseModel


class WorkflowNestedSerializer(BaseModel):
    id: UUIDB64
    name: str
    slug: str
    project_id: UUIDB64
    model_config = ConfigDict(from_attributes=True)


class WorkflowStatusNestedSerializer(BaseModel):
    id: UUIDB64
    name: str
    color: int
    order: int
    model_config = ConfigDict(from_attributes=True)

    @field_validator("order", mode="before")
    @classmethod
    def convert_decimal_int(cls, v: Decimal, info: ValidationInfo) -> int:
        """
        If there are some statuses ids repeated, ignore them,
        but keep the original order. Example:
        v = ["1", "1", "2", "1", "2"]
        return ["1", "2"]
        """
        return int(v)
