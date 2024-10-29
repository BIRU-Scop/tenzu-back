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

from typing import TYPE_CHECKING, Any

from base.api.permissions import PermissionComponent

if TYPE_CHECKING:
    from users.models import AnyUser


############################################################
# Generic permissions
############################################################


class AllowAny(PermissionComponent):
    async def is_authorized(self, user: "AnyUser", obj: Any = None) -> bool:
        return True


class DenyAll(PermissionComponent):
    async def is_authorized(self, user: "AnyUser", obj: Any = None) -> bool:
        return False


class IsSuperUser(PermissionComponent):
    async def is_authorized(self, user: "AnyUser", obj: Any = None) -> bool:
        return bool(user and user.is_authenticated and user.is_superuser)


class IsAuthenticated(PermissionComponent):
    async def is_authorized(self, user: "AnyUser", obj: Any = None) -> bool:
        return bool(user and user.is_authenticated)


class HasPerm(PermissionComponent):
    def __init__(self, perm: str, *components: "PermissionComponent") -> None:
        self.object_perm = perm
        super().__init__(*components)

    async def is_authorized(self, user: "AnyUser", obj: Any = None) -> bool:
        from permissions import services as permissions_services

        return await permissions_services.user_has_perm(user=user, perm=self.object_perm, obj=obj)


class IsRelatedToTheUser(PermissionComponent):
    def __init__(self, field: str, *components: "PermissionComponent") -> None:
        self.related_field = field
        super().__init__(*components)

    async def is_authorized(self, user: "AnyUser", obj: Any = None) -> bool:
        from permissions import services as permissions_services

        return await permissions_services.is_an_object_related_to_the_user(user=user, obj=obj, field=self.related_field)


class IsNotDeleted(PermissionComponent):
    """
    This permission is used to check if the object is not (logical) deleted.
    The object must have a `deleted_at` field, using the mixin
    `base.db.mixins.DeletedMetaInfoMixin`.
    """

    async def is_authorized(self, user: "AnyUser", obj: Any = None) -> bool:
        return not hasattr(obj, "deleted_at") or obj.deleted_at is None


############################################################
# Project permissions
############################################################


class CanViewProject(PermissionComponent):
    async def is_authorized(self, user: "AnyUser", obj: Any = None) -> bool:
        from permissions import services as permissions_services

        return await permissions_services.user_can_view_project(user=user, obj=obj)


class IsProjectAdmin(PermissionComponent):
    async def is_authorized(self, user: "AnyUser", obj: Any = None) -> bool:
        from permissions import services as permissions_services

        return await permissions_services.is_project_admin(user=user, obj=obj)


############################################################
# Workspace permissions
############################################################


class IsWorkspaceMember(PermissionComponent):
    async def is_authorized(self, user: "AnyUser", obj: Any = None) -> bool:
        from permissions import services as permissions_services

        return await permissions_services.is_workspace_member(user=user, obj=obj)
