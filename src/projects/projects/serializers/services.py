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

from projects.projects.models import Project
from projects.projects.serializers import ProjectDetailSerializer
from workflows.models import Workflow
from workspaces.workspaces.serializers.nested import WorkspaceNestedSerializer


def serialize_project_detail(
    project: Project,
    workspace: WorkspaceNestedSerializer,
    workflows: list[Workflow],
    user_is_admin: bool,
    user_is_member: bool,
    user_has_pending_invitation: bool,
    user_permissions: list[str],
) -> ProjectDetailSerializer:
    return ProjectDetailSerializer(
        id=project.id,
        name=project.name,
        slug=project.slug,
        description=project.description,
        color=project.color,
        logo=project.logo,
        landing_page=project.landing_page,
        workspace=workspace,
        workspace_id=workspace.id,
        workflows=workflows,
        user_is_admin=user_is_admin,
        user_is_member=user_is_member,
        user_has_pending_invitation=user_has_pending_invitation,
        user_permissions=user_permissions,
    )
