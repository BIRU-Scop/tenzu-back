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

from typing import Any

from humps.main import camelize
from pydantic import BaseModel as _BaseModel
from pydantic import ConfigDict


class BaseModel(_BaseModel):
    async def cleaned_dict(self, request) -> dict[str, Any]:
        """
        This method chooses the valid fields from the form. Used in PATCH endpoints for instance.
        Pydantic forms always fill all the fields, even with None. In a PATCH we need to distinguish between:
        a) no data: means the original value stays
        b) data with None: means delete de value
        This method reads the fields in the request.form and filter them from the Pytantic form
        """
        keys = (await request.form()).keys()
        return {k: v for k, v in self.model_dump().items() if k in keys}

    model_config = ConfigDict(alias_generator=camelize, populate_by_name=True)
