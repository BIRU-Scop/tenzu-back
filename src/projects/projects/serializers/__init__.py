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

from memberships.serializers import RoleSerializer
from projects.projects.serializers.mixins import ProjectLogoBaseSerializer  # noqa
from projects.projects.serializers.nested import ProjectNestedSerializer
from workflows.serializers.nested import WorkflowNestedSerializer
from workspaces.workspaces.serializers.nested import WorkspaceNestedSerializer


class ProjectSummarySerializer(ProjectNestedSerializer):
    user_is_invited: bool
    model_config = ConfigDict(from_attributes=True)


class ProjectDetailSerializer(ProjectSummarySerializer):
    workspace: WorkspaceNestedSerializer
    workflows: list[WorkflowNestedSerializer]

    user_role: RoleSerializer | None
    model_config = ConfigDict(from_attributes=True)
