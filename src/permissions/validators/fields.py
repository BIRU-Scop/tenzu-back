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

from typing import Annotated, Any, Callable, Generator, TypeVar

from pydantic import (
    AfterValidator,
)
from pydantic.json_schema import WithJsonSchema

from commons.validators import check_not_empty
from permissions import choices

CallableGenerator = Generator[Callable[..., Any], None, None]

P = TypeVar("P", bound=choices.PermissionsBase)


def validate_permissions(permissions_type: type[P], value: list[str]) -> set[P]:
    value = set(check_not_empty(value))
    _check_permissions_are_valid(permissions_type, permissions=value)
    _check_permissions_are_compatible(permissions_type, permissions=value)
    return value


ProjectPermissionsField = Annotated[
    list[str],
    AfterValidator(
        lambda value: validate_permissions(choices.ProjectPermissions, value)
    ),
    WithJsonSchema({"example": [choices.ProjectPermissions.VIEW_STORY.value]}),
]
WorkspacePermissionsField = Annotated[
    list[str],
    AfterValidator(
        lambda value: validate_permissions(choices.WorkspacePermissions, value)
    ),
    WithJsonSchema({"example": [choices.WorkspacePermissions.CREATE_PROJECT.value]}),
]


def _check_permissions_are_valid(
    permissions_type: type[P], permissions: set[str]
) -> None:
    invalid_permissions = permissions - set(permissions_type)
    if invalid_permissions:
        raise ValueError(
            f"The following permissions are not valid: {invalid_permissions}."
        )


def _check_permissions_are_compatible(
    permissions_type: type[P], permissions: set[str]
) -> None:
    for permission, required_permission in permissions_type.dependencies():
        if permission in permissions and required_permission not in permissions:
            raise ValueError(f"{permission} needs {required_permission} permission")
