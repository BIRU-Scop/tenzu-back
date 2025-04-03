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

import abc
from typing import TYPE_CHECKING, Any

from commons.exceptions import api as ex

if TYPE_CHECKING:
    from users.models import AnyUser

######################################################################
# Permission components - basic class
######################################################################


class PermissionComponent(metaclass=abc.ABCMeta):
    error = ex.ForbiddenError("User doesn't have permissions to perform this action")

    @abc.abstractmethod
    async def is_authorized(self, user: "AnyUser", obj: Any = None) -> bool:
        raise NotImplementedError

    def __invert__(self) -> "Not":
        return Not(self)

    def __and__(self, component: "PermissionComponent") -> "And":
        return And(self, component)

    def __or__(self, component: "PermissionComponent") -> "Or":
        return Or(self, component)


######################################################################
# Permission components - operators
######################################################################


class PermissionOperator(PermissionComponent):
    """
    Base class for all logical operators for compose components.
    """

    def __init__(self, *components: "PermissionComponent") -> None:
        self.components = tuple(components)


class Not(PermissionOperator):
    """
    Negation operator as permission component.
    """

    # Overwrites the default constructor for fix
    # to one parameter instead of variable list of them.
    def __init__(self, component: "PermissionComponent") -> None:
        super().__init__(component)

    async def is_authorized(self, user: "AnyUser", obj: Any = None) -> bool:
        component = self.components[0]
        return not await component.is_authorized(user, obj)


class Or(PermissionOperator):
    """
    Or logical operator as permission component.
    """

    async def is_authorized(self, user: "AnyUser", obj: Any = None) -> bool:
        valid = False

        for component in self.components:
            if await component.is_authorized(user, obj):
                valid = True
                break

        return valid


class And(PermissionOperator):
    """
    And logical operator as permission component.
    """

    async def is_authorized(self, user: "AnyUser", obj: Any = None) -> bool:
        valid = True

        for component in self.components:
            if not await component.is_authorized(user, obj):
                self.error = component.error
                valid = False
                break

        return valid


######################################################################
# check_permissions - main function
######################################################################


async def check_permissions(
    permissions: PermissionComponent,
    user: "AnyUser",
    obj: object = None,
) -> None:
    if user.is_superuser:
        return

    if not await permissions.is_authorized(user=user, obj=obj):
        raise permissions.error


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
        return bool(user and user.is_superuser)


class IsAuthenticated(PermissionComponent):
    # NOTE: We force a 401 instead of using the default (which would return a 403)
    error = ex.AuthorizationError("User is anonymous")

    async def is_authorized(self, user: "AnyUser", obj: Any = None) -> bool:
        return bool(user and user.is_authenticated)


class IsRelatedToTheUser(PermissionComponent):
    def __init__(self, field: str = "user", *components: "PermissionComponent") -> None:
        self.related_field = field
        super().__init__(*components)

    async def is_authorized(self, user: "AnyUser", obj: Any = None) -> bool:
        return obj and getattr(obj, self.related_field) == user


class IsNotDeleted(PermissionComponent):
    """
    This permission is used to check if the object is not (logical) deleted.
    The object must have a `deleted_at` field, using the mixin
    `base.db.mixins.DeletedMetaInfoMixin`.
    """

    async def is_authorized(self, user: "AnyUser", obj: Any = None) -> bool:
        return not hasattr(obj, "deleted_at") or obj.deleted_at is None
