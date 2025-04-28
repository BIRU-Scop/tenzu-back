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

from workspaces.workspaces.api.validators import (
    UpdateWorkspaceValidator,
    WorkspaceValidator,
)

##########################################################
# WorkspaceValidator
##########################################################


def test_validate_workspace_with_empty_name(client):
    name = ""
    color = 1

    with pytest.raises(ValidationError):
        WorkspaceValidator(name=name, color=color)


def test_validate_workspace_with_long_name(client):
    name = "WS ab c de f gh i jk l mn pw r st u vw x yz"
    color = 1

    with pytest.raises(ValidationError, match=r"should have at most 40 characters"):
        WorkspaceValidator(name=name, color=color)


def test_validate_workspace_with_invalid_color(client):
    name = "WS test"
    color = 9

    with pytest.raises(
        ValidationError, match=r"Input should be less than or equal to 8"
    ):
        WorkspaceValidator(name=name, color=color)


def test_validate_workspace_with_color_string(client):
    name = "WS test"
    color = "0F0F0F"

    with pytest.raises(ValidationError, match=r"Input should be a valid integer"):
        WorkspaceValidator(name=name, color=color)


def test_validate_workspace_with_valid_data(client):
    name = "WS test"
    color = 1

    data = WorkspaceValidator(name=name, color=color)
    assert data.name == name
    assert data.color == color


def test_validate_workspace_with_blank_chars(client):
    name = "       My w0r#%&乕شspace         "
    color = 1

    data = WorkspaceValidator(name=name, color=color)
    assert data.name == "My w0r#%&乕شspace"
    assert data.color == color


##########################################################
# UpdateWorkspaceValidator
##########################################################


def test_validate_update_workspace_ok():
    name = "new name"
    patch = UpdateWorkspaceValidator(name=name)

    assert patch.name == name


def test_validate_update_workspace_with_empty_name(client):
    name = ""

    with pytest.raises(ValidationError):
        UpdateWorkspaceValidator(name=name)
