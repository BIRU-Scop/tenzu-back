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

from enum import Enum

from memberships.permissions import CanModifyAssociatedRole, HasPermission, IsMember
from permissions import (
    IsAuthenticated,
    IsRelatedToTheUser,
)
from permissions.choices import WorkspacePermissions


class WorkspaceMembershipPermissionsCheck(Enum):
    VIEW = IsAuthenticated() & IsMember("workspace")
    MODIFY = (
        IsAuthenticated()
        & HasPermission(
            "workspace", WorkspacePermissions.CREATE_MODIFY_MEMBER, field="workspace"
        )
        & CanModifyAssociatedRole("workspace")
    )
    DELETE = IsAuthenticated() & (
        (
            HasPermission(
                "workspace", WorkspacePermissions.DELETE_MEMBER, field="workspace"
            )
            & CanModifyAssociatedRole("workspace")
        )
        | IsRelatedToTheUser("user")
    )


class WorkspaceRolePermissionsCheck(Enum):
    VIEW = IsAuthenticated() & IsMember(
        "workspace",
    )
