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

from enum import Enum

from memberships.permissions import HasPermission
from permissions import IsAuthenticated, PermissionComponent
from permissions.choices import ProjectPermissions
from projects.invitations.models import ProjectInvitation
from projects.memberships.permissions import CanModifyAssociatedRole
from projects.projects.models import Project
from users.models import AnyUser


class IsProjectInvitationRecipient(PermissionComponent):
    async def is_authorized(self, user: AnyUser, obj: ProjectInvitation = None) -> bool:
        from projects.invitations import services as invitations_services

        if not obj:
            return False

        return invitations_services.is_invitation_for_this_user(
            invitation=obj, user=user
        )


class HasPendingProjectInvitation(PermissionComponent):
    async def is_authorized(self, user: AnyUser, obj: Project = None) -> bool:
        from projects.invitations import services as invitations_services

        if not obj:
            return False

        return await invitations_services.has_pending_invitation(
            user=user, reference_object=obj
        )


class InvitationPermissionsCheck(Enum):
    VIEW = IsAuthenticated() & HasPermission(ProjectPermissions.CREATE_MODIFY_MEMBER)
    ANSWER_SELF = IsAuthenticated()
    ANSWER = IsAuthenticated() & IsProjectInvitationRecipient()
    CREATE = IsAuthenticated() & HasPermission(ProjectPermissions.CREATE_MODIFY_MEMBER)
    MODIFY = (
        IsAuthenticated()
        & HasPermission(ProjectPermissions.CREATE_MODIFY_MEMBER, field="project")
        & CanModifyAssociatedRole()
    )
