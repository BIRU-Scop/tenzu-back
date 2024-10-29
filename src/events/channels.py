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
from users.models import AnyUser, User
from workspaces.workspaces.models import Workspace

_SYSTEM_CHANNEL_PATTERN = "system"
_USER_CHANNEL_PATTERN = "users.{username}"
_PROJECT_CHANNEL_PATTERN = "projects.{id}"
_WORKSPACE_CHANNEL_PATTERN = "workspaces.{id}"


def system_channel() -> str:
    return _SYSTEM_CHANNEL_PATTERN


def user_channel(user: AnyUser | str) -> str:
    username = user.username if isinstance(user, User) else user
    return _USER_CHANNEL_PATTERN.format(username=username)


def project_channel(project: Project | str) -> str:
    id = project.b64id if isinstance(project, Project) else project
    return _PROJECT_CHANNEL_PATTERN.format(id=id)


def workspace_channel(workspace: Workspace | str) -> str:
    id = workspace.b64id if isinstance(workspace, Workspace) else workspace
    return _WORKSPACE_CHANNEL_PATTERN.format(id=id)
