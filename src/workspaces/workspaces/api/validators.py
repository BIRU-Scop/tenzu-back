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

from pydantic import Field, StringConstraints
from typing_extensions import Annotated

from base.validators import BaseModel

Name = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=40)
]
# class Name(ConstrainedStr):
#     strip_whitespace = True
#     min_length = 1
#     max_length = 40


class WorkspaceValidator(BaseModel):
    name: Name
    color: Annotated[int, Field(gt=0, lt=9)]  # type: ignore


class UpdateWorkspaceValidator(BaseModel):
    name: Name | None
