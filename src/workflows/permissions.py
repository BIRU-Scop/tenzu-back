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

from memberships.permissions import HasPermission
from permissions import IsAuthenticated
from permissions.choices import ProjectPermissions


class WorkflowPermissionsCheck(Enum):
    VIEW = IsAuthenticated() & HasPermission(
        "project", ProjectPermissions.VIEW_WORKFLOW
    )
    MODIFY = IsAuthenticated() & HasPermission(
        "project", ProjectPermissions.MODIFY_WORKFLOW
    )
    DELETE = IsAuthenticated() & HasPermission(
        "project", ProjectPermissions.DELETE_WORKFLOW
    )
    CREATE = IsAuthenticated() & HasPermission(
        "project", ProjectPermissions.CREATE_WORKFLOW
    )
