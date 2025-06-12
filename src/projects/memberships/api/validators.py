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
from typing import Annotated

from pydantic import StringConstraints

from commons.validators import B64UUID, BaseModel
from permissions.validators import ProjectPermissionsField

_RoleName = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)
]


class UpdateRoleValidator(BaseModel):
    name: _RoleName | None = None
    permissions: ProjectPermissionsField | None = None


class CreateRoleValidator(BaseModel):
    name: _RoleName
    permissions: ProjectPermissionsField


class DeleteRoleQuery(BaseModel):
    move_to: B64UUID | None = None
