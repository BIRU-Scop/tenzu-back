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
from permissions.choices import WorkspacePermissions
from users.models import AnyUser
from workspaces.invitations.models import WorkspaceInvitation
from workspaces.workspaces.models import Workspace


class IsWorkspaceInvitationRecipient(PermissionComponent):
    async def is_authorized(
        self, user: AnyUser, obj: WorkspaceInvitation = None
    ) -> bool:
        from workspaces.invitations import services as invitations_services

        if not obj:
            return False

        return invitations_services.is_invitation_for_this_user(
            invitation=obj, user=user
        )


class HasPendingWorkspaceInvitation(PermissionComponent):
    async def is_authorized(self, user: AnyUser, obj: Workspace = None) -> bool:
        from workspaces.invitations import services as invitations_services

        if not obj:
            return False

        return await invitations_services.has_pending_invitation(
            user=user, reference_object=obj
        )


class CanModifyInvitation(PermissionComponent):
    async def is_authorized(
        self, user: AnyUser, obj: WorkspaceInvitation = None
    ) -> bool:
        # must always be called after HasPermission to fill this attribute
        user_role = user.workspace_role
        # user can only modify invitation of owner if they are owner themselves
        return user_role.is_owner or (not obj.role.is_owner)


class InvitationPermissionsCheck(Enum):
    VIEW = IsAuthenticated() & HasPermission(WorkspacePermissions.CREATE_MODIFY_MEMBER)
    ANSWER_SELF = IsAuthenticated()
    ANSWER = IsAuthenticated() & IsWorkspaceInvitationRecipient()
    CREATE = IsAuthenticated() & HasPermission(
        WorkspacePermissions.CREATE_MODIFY_MEMBER
    )
    MODIFY = (
        IsAuthenticated()
        & HasPermission(WorkspacePermissions.CREATE_MODIFY_MEMBER, field="workspace")
        & CanModifyInvitation()
    )
