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

from projects.invitations.api.validators import ProjectInvitationsValidator, ProjectInvitationValidator
from tests.unit.utils import check_validation_errors


@pytest.mark.parametrize(
    "email, username, role_slug, error_fields, expected_errors",
    [
        ("email@test.com", "username", "", ["roleSlug"], "Empty field is not allowed"),
        (
            "email@test.com",
            "username",
            None,
            ["roleSlug"],
            "none is not an allowed value",
        ),
        (
            "not an email",
            "username",
            "role",
            ["email"],
            "value is not a valid email address",
        ),
    ],
)
def test_email_role_slug(email, username, role_slug, error_fields, expected_errors):
    with pytest.raises(ValidationError) as validation_errors:
        ProjectInvitationValidator(email=email, username=username, role_slug=role_slug)

    expected_error_fields = error_fields
    expected_error_messages = expected_errors
    check_validation_errors(validation_errors, expected_error_fields, expected_error_messages)


def test_validate_invitations_more_than_50():
    invitations = []
    for i in range(55):
        invitations.append({"email": f"test{i}@email.com", "role_slug": "general"})

    with pytest.raises(ValidationError, match=r"value_error.list.max_items") as validation_errors:
        ProjectInvitationsValidator(invitations=invitations)

    expected_error_fields = ["invitations"]
    expected_error_messages = ["ensure this value has at most 50 items"]
    check_validation_errors(validation_errors, expected_error_fields, expected_error_messages)
