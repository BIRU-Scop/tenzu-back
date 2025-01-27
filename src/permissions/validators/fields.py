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

from typing import Annotated, Any, Callable, Generator

from pydantic import (
    AfterValidator,
)
from pydantic.json_schema import WithJsonSchema

from permissions import choices

CallableGenerator = Generator[Callable[..., Any], None, None]


def validate_permissions(value: list[str]):
    if not _permissions_are_valid(permissions=value):
        raise ValueError(
            "One or more permissions are not valid. Maybe, there is a typo."
        )
    if not _permissions_are_compatible(permissions=value):
        raise ValueError("Given permissions are incompatible")
    return value


Permissions = Annotated[
    list[str],
    AfterValidator(validate_permissions),
    WithJsonSchema({"example": ["view_story"]}),
]


def _permissions_are_valid(permissions: list[str]) -> bool:
    return set.issubset(set(permissions), set(choices.ProjectPermissions))


def _permissions_are_compatible(permissions: list[str]) -> bool:
    # a user cannot edit a story if she has no view permission
    if "view_story" not in permissions and set.intersection(
        set(permissions), choices.EditStoryPermissions
    ):
        return False

    # a user cannot have "comment_story" permissions if she has no "view_story" permission
    if "comment_story" in permissions and "view_story" not in permissions:
        return False

    return True
