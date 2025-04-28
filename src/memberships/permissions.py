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
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from memberships.models import Invitation, Membership, Role
from permissions import PermissionComponent
from permissions.choices import PermissionsBase
from projects.projects.models import Project
from workspaces.workspaces.models import Workspace

if TYPE_CHECKING:
    from users.models import AnyUser

logger = logging.getLogger(__name__)


class IsMember(PermissionComponent):
    """
    This permission is used to check if the user is a member of the object
    The object must implement the membership+role api.
    As a side-effect, set a *_role property on the user
    """

    def __init__(
        self,
        model_name: str,
        access_fields: str | tuple[str, ...] = None,
        *components: "PermissionComponent",
    ) -> None:
        self.model_name = model_name
        self.access_fields = access_fields
        self.role: Role | None = None
        super().__init__(*components)

    async def is_authorized(self, user: "AnyUser", obj: Any = None) -> bool:
        from memberships import repositories as memberships_repositories

        if not obj:
            return False

        if self.access_fields is not None:
            if isinstance(self.access_fields, str):
                self.access_fields: tuple[str, ...] = (self.access_fields,)
            for field in self.access_fields:
                obj = getattr(obj, field)

        obj: Workspace | Project

        model_name = obj._meta.model_name
        if model_name != self.model_name:
            msg = f"Expecting to check permission on {self.model_name}, received {model_name}"
            logger.error(msg)
            raise ValueError(msg)
        try:
            self.role = await memberships_repositories.get_role(
                obj.roles.model,
                filters={"memberships__user_id": user.id, f"{model_name}_id": obj.id},
            )
        except obj.roles.model.DoesNotExist:
            return False
        setattr(user, f"{model_name}_role", self.role)
        return True


class HasPermission(IsMember):
    """
    This permission is used to check if the user has the given permissions on the object.
    The object must implement the membership+role api.
    As a side-effect, set a *_role property on the user
    """

    def __init__(
        self,
        model_name: str,
        permission: PermissionsBase,
        access_fields: str | tuple[str, ...] = None,
        *components: "PermissionComponent",
    ) -> None:
        self.required_permission = permission
        super().__init__(model_name, access_fields, *components)

    async def is_authorized(self, user: "AnyUser", obj: Any = None) -> bool:
        if not await super().is_authorized(user, obj):
            return False
        return self.required_permission in self.role.permissions


class CanModifyAssociatedRole(PermissionComponent):
    def __init__(
        self,
        model_name: str,
        *components: "PermissionComponent",
    ) -> None:
        self.model_name = model_name
        super().__init__(*components)

    async def is_authorized(
        self, user: AnyUser, obj: Invitation | Membership = None
    ) -> bool:
        # must always be called after a related IsMember or HasPermission to fill this attribute
        user_role: Role = getattr(user, f"{self.model_name}_role")
        # user can only modify invitation of owner if they are owner themselves
        return user_role.is_owner or (not obj.role.is_owner)


class IsInvitationRecipient(PermissionComponent):
    async def is_authorized(self, user: AnyUser, obj: Invitation = None) -> bool:
        from memberships import services as invitations_services

        if not obj:
            return False

        return invitations_services.is_invitation_for_this_user(
            invitation=obj, user=user
        )


class HasPendingInvitation(PermissionComponent):
    """
    This permission is used to check if the user has been invited to the object.
    The object must implement the membership+role api.
    As a side-effect, set a is_invited property on the user
    """

    async def is_authorized(
        self, user: AnyUser, obj: Project | Workspace = None
    ) -> bool:
        from memberships import services as invitations_services

        if not obj:
            return False

        has_pending_invitation = await invitations_services.has_pending_invitation(
            user=user, reference_object=obj
        )
        user.is_invited = has_pending_invitation
        return has_pending_invitation
