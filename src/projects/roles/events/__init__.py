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

from events import events_manager
from projects.roles.events.content import ProjectRoleContent
from projects.roles.models import ProjectRole

UPDATE_PROJECT_ROLE_PERMISSIONS = "projectroles.update"


async def emit_event_when_project_role_permissions_are_updated(
    role: ProjectRole,
) -> None:
    """
    This event is emitted whenever the permissions list changes for a role
    :param role: The project role affected by the permission change
    """
    await events_manager.publish_on_project_channel(
        project=role.project,
        type=UPDATE_PROJECT_ROLE_PERMISSIONS,
        content=ProjectRoleContent.from_orm(role),
    )
