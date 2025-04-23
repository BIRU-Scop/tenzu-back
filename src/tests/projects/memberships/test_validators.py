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

from permissions.choices import ProjectPermissions
from projects.memberships.api import RoleUpdateValidator
from tests.utils.utils import check_validation_errors

##########################################################
# RoleValidator
##########################################################


def test_validate_role_ok():
    name = "new name"
    permissions = [ProjectPermissions.VIEW_STORY]
    patch = RoleUpdateValidator(name=name, permissions=permissions)

    assert patch.name == name
    assert patch.permissions == permissions


def test_validate_role_ko_empty_permission():
    name = "new name"
    permissions = []

    with pytest.raises(ValidationError) as validations_errors:
        RoleUpdateValidator(name=name, permissions=permissions)

    expected_error_fields = ["permissions"]
    expected_error_messages = [
        "Value error, Empty field is not allowed",
    ]
    check_validation_errors(
        validations_errors, expected_error_fields, expected_error_messages
    )


def test_validate_role_ok_not_set():
    patch = RoleUpdateValidator()

    assert patch.name is None
    assert patch.permissions is None
    assert patch.model_dump(exclude_unset=True) == {}
