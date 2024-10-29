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

import pytest
from pydantic import ValidationError

from base.serializers import BaseModel
from permissions.validators import Permissions

#####################################################################
# Permissions
#####################################################################


class PermissionsValidator(BaseModel):
    permissions: Permissions


@pytest.mark.parametrize(
    "permissions, result",
    [
        ([], []),
        (["comment_story", "view_story"], ["comment_story", "view_story"]),
        (["view_story", "modify_story"], ["view_story", "modify_story"]),
    ],
)
def test_permissions_are_valid_and_compatible(permissions: list[str], result: list[str]):
    validator = PermissionsValidator(permissions=permissions)
    assert validator.permissions == result


@pytest.mark.parametrize(
    "permissions",
    [
        None,
        [None],
        [""],
        ["comment_story", "not_valid"],
        ["non_existent"],
        ["view_story", "foo"],
        ["add_story", "modify_story", "comment_story"],
    ],
)
def test_permissions_are_invalid_or_not_compatible(
    permissions: list[str] | None,
) -> None:
    with pytest.raises(ValidationError):
        PermissionsValidator(permissions=permissions)
