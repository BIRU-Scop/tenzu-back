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
from projects.projects.serializers.mixins import ProjectLogoMixin
from workflows.serializers.nested import WorkflowNestedSerializer
from workspaces.workspaces.serializers.nested import WorkspaceNestedSerializer


class ProjectSummarySerializer(BaseModel, ProjectLogoMixin):
    id: UUIDB64
    name: str
    slug: str
    description: str
    color: int
    workspace_id: UUIDB64
    model_config = ConfigDict(from_attributes=True)


class ProjectDetailSerializer(BaseModel, ProjectLogoMixin):
    id: UUIDB64
    name: str
    slug: str
    description: str
    color: int
    landing_page: str
    workspace_id: UUIDB64
    workspace: WorkspaceNestedSerializer
    workflows: list[WorkflowNestedSerializer]

    # User related fields
    user_is_admin: bool
    user_is_member: bool
    user_has_pending_invitation: bool
    user_permissions: list[str]
    model_config = ConfigDict(from_attributes=True)
