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
from typing import TYPE_CHECKING

from memberships.permissions import (
    CanModifyAssociatedRole,
    HasPermission,
    IsInvitationRecipient,
)
from permissions import IsAuthenticated, PermissionComponent
from permissions.choices import WorkspacePermissions
from workspaces.workspaces.models import Workspace

if TYPE_CHECKING:
    from users.models import AnyUser


class HasPendingInnerProjectsInvitation(PermissionComponent):
    async def is_authorized(self, user: "AnyUser", obj: Workspace = None) -> bool:
        from workspaces.invitations import services as invitations_services

        if not obj:
            return False

        return await invitations_services.has_pending_inner_projects_invitation(
            user=user, workspace=obj
        )


class WorkspaceInvitationPermissionsCheck(Enum):
    VIEW = IsAuthenticated() & HasPermission(
        "workspace", WorkspacePermissions.CREATE_MODIFY_MEMBER
    )
    ANSWER_SELF = IsAuthenticated()
    ANSWER = IsAuthenticated() & IsInvitationRecipient()
    CREATE = IsAuthenticated() & HasPermission(
        "workspace", WorkspacePermissions.CREATE_MODIFY_MEMBER
    )
    MODIFY = (
        IsAuthenticated()
        & HasPermission(
            "workspace",
            WorkspacePermissions.CREATE_MODIFY_MEMBER,
            access_fields="workspace",
        )
        & CanModifyAssociatedRole("workspace")
    )
