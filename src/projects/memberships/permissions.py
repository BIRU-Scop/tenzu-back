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
from permissions.choices import ProjectPermissions


class ProjectMembershipPermissionsCheck(Enum):
    VIEW = IsAuthenticated() & IsMember("project")
    MODIFY = (
        IsAuthenticated()
        & HasPermission(
            "project", ProjectPermissions.CREATE_MODIFY_MEMBER, field="project"
        )
        & CanModifyAssociatedRole("project")
    )
    DELETE = IsAuthenticated() & (
        (
            HasPermission("project", ProjectPermissions.DELETE_MEMBER, field="project")
            & CanModifyAssociatedRole("project")
        )
        | IsRelatedToTheUser("user")
    )


class ProjectRolePermissionsCheck(Enum):
    VIEW = IsAuthenticated() & IsMember("project")
    CREATE = IsAuthenticated() & HasPermission(
        "project", ProjectPermissions.CREATE_MODIFY_DELETE_ROLE
    )
    MODIFY = IsAuthenticated() & HasPermission(
        "project", ProjectPermissions.CREATE_MODIFY_DELETE_ROLE, field="project"
    )
    DELETE = IsAuthenticated() & HasPermission(
        "project", ProjectPermissions.CREATE_MODIFY_DELETE_ROLE, field="project"
    )
