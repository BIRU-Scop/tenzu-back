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

from tests.utils.utils import check_validation_errors
from workspaces.invitations.api.validators import (
    WorkspaceInvitationsValidator,
    WorkspaceInvitationValidator,
)


@pytest.mark.parametrize(
    "username_or_email, error_fields, expected_errors",
    [
        ("", ["email"], "Empty field is not allowed"),
        (None, ["email"], "none is not an allowed value"),
    ],
)
def test_email(username_or_email, error_fields, expected_errors):
    with pytest.raises(ValidationError) as validation_errors:
        WorkspaceInvitationValidator(username_or_email=username_or_email)

    expected_error_fields = error_fields
    expected_error_messages = expected_errors
    check_validation_errors(
        validation_errors, expected_error_fields, expected_error_messages
    )


def test_validate_invitations_more_than_50():
    invitations = []
    for i in range(55):
        invitations.append({"username_or_email": f"test{i}@email.com"})

    with pytest.raises(
        ValidationError, match=r"type=too_long.+input_type=list"
    ) as validation_errors:
        WorkspaceInvitationsValidator(invitations=invitations)

    expected_error_fields = ["invitations"]
    expected_error_messages = [
        "List should have at most 50 items after validation, not 55"
    ]
    check_validation_errors(
        validation_errors, expected_error_fields, expected_error_messages
    )
