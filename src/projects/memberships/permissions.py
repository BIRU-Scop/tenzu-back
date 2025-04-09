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
from permissions import (
    IsAuthenticated,
    IsRelatedToTheUser,
    PermissionComponent,
)
from permissions.choices import ProjectPermissions
from projects.invitations.models import ProjectInvitation
from projects.memberships.models import ProjectMembership
from projects.projects.models import Project
from users.models import AnyUser, User


class IsProjectMember(PermissionComponent):
    async def is_authorized(self, user: "AnyUser", obj: Project = None) -> bool:
        if not obj:
            return False
        return await obj.roles.filter(users=user).aexists()


class CanModifyAssociatedRole(PermissionComponent):
    async def is_authorized(
        self, user: User, obj: ProjectInvitation | ProjectMembership = None
    ) -> bool:
        # must always be called after HasPermission to fill this attribute
        user_role = user.project_role
        # user can only modify invitation of owner if they are owner themselves
        return user_role.is_owner or (not obj.role.is_owner)


class ProjectMembershipPermissionsCheck(Enum):
    VIEW = IsProjectMember()
    MODIFY = (
        IsAuthenticated()
        & HasPermission(ProjectPermissions.CREATE_MODIFY_MEMBER, field="project")
        & CanModifyAssociatedRole()
    )
    DELETE = IsAuthenticated() & (
        (
            HasPermission(ProjectPermissions.DELETE_MEMBER, field="project")
            & CanModifyAssociatedRole()
        )
        | IsRelatedToTheUser("user")
    )


class ProjectRolePermissionsCheck(Enum):
    VIEW = IsProjectMember()
    CREATE = IsAuthenticated() & HasPermission(
        ProjectPermissions.CREATE_MODIFY_DELETE_ROLE
    )
    MODIFY = IsAuthenticated() & HasPermission(
        ProjectPermissions.CREATE_MODIFY_DELETE_ROLE, field="project"
    )
    DELETE = IsAuthenticated() & HasPermission(
        ProjectPermissions.CREATE_MODIFY_DELETE_ROLE, field="project"
    )
