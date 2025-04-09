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

from typing import TYPE_CHECKING, Any

from permissions import PermissionComponent
from permissions.choices import PermissionsBase
from projects.projects.models import Project
from workspaces.workspaces.models import Workspace

if TYPE_CHECKING:
    from users.models import AnyUser


class HasPermission(PermissionComponent):
    """
    This permission is used to check if the user has the given permissions on the object.
    The object must implement the membership+role api.
    As a side-effect, set a *_role property on the user
    """

    def __init__(
        self,
        permission: PermissionsBase,
        field: str = None,
        *components: "PermissionComponent",
    ) -> None:
        self.required_permission = permission
        self.field = field
        super().__init__(*components)

    async def is_authorized(self, user: "AnyUser", obj: Any = None) -> bool:
        from memberships import repositories as memberships_repositories

        if not obj:
            return False

        obj: Workspace | Project = (
            obj if self.field is None else getattr(obj, self.field)
        )

        model_name = obj._meta.model_name
        try:
            user_role = await memberships_repositories.get_role(
                obj.roles.model,
                filters={"memberships__user_id": user.id, f"{model_name}_id": obj.id},
            )
        except obj.roles.model.DoesNotExist:
            return False
        setattr(user, f"{model_name}_role", user_role)
        return self.required_permission in user_role.permissions
