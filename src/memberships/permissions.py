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

from typing import TYPE_CHECKING

from permissions import PermissionComponent
from permissions.choices import PermissionsBase
from projects.projects.models import Project
from workspaces.workspaces.models import Workspace

if TYPE_CHECKING:
    from users.models import AnyUser


class HasPermission(PermissionComponent):
    """
    This permission is used to check if the user has the given permissions on the object.
    The object must implement the membership+role api
    """

    def __init__(
        self, permission: PermissionsBase, *components: "PermissionComponent"
    ) -> None:
        self.required_permission = permission
        super().__init__(*components)

    async def is_authorized(
        self, user: "AnyUser", obj: Workspace | Project = None
    ) -> bool:
        from memberships import services as memberships_services

        if not obj:
            return False

        return await memberships_services.has_permission(
            user=user,
            reference_object=obj,
            required_permission=self.required_permission,
        )
