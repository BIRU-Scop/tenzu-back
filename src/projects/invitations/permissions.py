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
from typing import Any
from uuid import UUID

from permissions import IsAuthenticated, PermissionComponent
from projects.invitations.models import ProjectInvitation
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


class CanAssignMember(PermissionComponent):
    async def is_authorized(self, user: AnyUser, obj: Any = None) -> bool:
        # obj is project_id
        obj: UUID
        # TODO use role permission
        return False


class CanModifyInvitation(PermissionComponent):
    async def is_authorized(self, user: AnyUser, obj: Any = None) -> bool:
        # obj is invitation
        obj: ProjectInvitation
        # TODO compare role of user and invitation.user
        # if user.role.is_owner -> return True
        # if user.role doesn't have invite permission -> return False
        # if invitation.user.role.is_owner -> return False
        # return True
        return False


class InvitationPermissionsCheck(Enum):
    VIEW = CanAssignMember()
    ANSWER_SELF = IsAuthenticated()
    ANSWER = IsAuthenticated() & IsProjectInvitationRecipient()
    CREATE = CanAssignMember()
    MODIFY = CanModifyInvitation()
