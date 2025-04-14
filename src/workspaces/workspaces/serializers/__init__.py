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

from pydantic import ConfigDict

from base.serializers import UUIDB64, BaseModel
from projects.projects.serializers.nested import ProjectNestedSerializer


class WorkspaceDetailSerializer(BaseModel):
    id: UUIDB64
    name: str
    slug: str
    color: int
    latest_projects: list[ProjectNestedSerializer]
    invited_projects: list[ProjectNestedSerializer]
    total_projects: int
    has_projects: bool
    user_role: str
    model_config = ConfigDict(from_attributes=True)


class WorkspaceSerializer(BaseModel):
    id: UUIDB64
    name: str
    slug: str
    color: int
    total_projects: int
    has_projects: bool
    user_role: str | None
    model_config = ConfigDict(from_attributes=True)
