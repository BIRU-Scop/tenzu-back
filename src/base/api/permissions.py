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
from typing import Any

from exceptions import api as ex
from users.models import AnyUser

######################################################################
# Permission components - basic class
######################################################################


class PermissionComponent(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    async def is_authorized(self, user: AnyUser, obj: Any = None) -> bool:
        pass

    def __invert__(self) -> "Not":
        return Not(self)

    def __and__(self, component: "PermissionComponent") -> "And":
        return And(self, component)

    def __or__(self, component: "PermissionComponent") -> "Or":
        return Or(self, component)


######################################################################
# check_permissions - main function
######################################################################


async def check_permissions(
    permissions: PermissionComponent,
    user: AnyUser,
    obj: object = None,
    global_perms: PermissionComponent | None = None,
    enough_perms: PermissionComponent | None = None,
) -> None:
    if user.is_superuser:
        return

    _required_permissions = permissions

    if global_perms:
        _required_permissions = global_perms & _required_permissions

    if enough_perms:
        _required_permissions = enough_perms | _required_permissions

    if not await _required_permissions.is_authorized(user=user, obj=obj):
        raise ex.ForbiddenError("User doesn't have permissions to perform this action")


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

    async def is_authorized(self, user: AnyUser, obj: Any = None) -> bool:
        component = self.components[0]
        return not await component.is_authorized(user, obj)


class Or(PermissionOperator):
    """
    Or logical operator as permission component.
    """

    async def is_authorized(self, user: AnyUser, obj: Any = None) -> bool:
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

    async def is_authorized(self, user: AnyUser, obj: Any = None) -> bool:
        valid = True

        for component in self.components:
            if not await component.is_authorized(user, obj):
                valid = False
                break

        return valid
