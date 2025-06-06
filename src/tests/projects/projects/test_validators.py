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

from projects.projects.api.validators import (
    CreateProjectValidator,
    UpdateProjectValidator,
)
from tests.utils import factories as f
from tests.utils.utils import check_validation_errors

##########################################################
# ProjectValidator
##########################################################


def test_validate_create_user_wrong_not_all_required_fields():
    with pytest.raises(ValidationError) as validation_errors:
        CreateProjectValidator()

    expected_error_fields = ["name"]
    expected_error_messages = ["Field required"]
    check_validation_errors(
        validation_errors, expected_error_fields, expected_error_messages
    )


def test_validate_project_with_empty_name():
    name = ""
    color = 1

    with pytest.raises(
        ValidationError, match=r"String should have at least 1 character"
    ):
        # noinspection PyArgumentList
        CreateProjectValidator(name=name, color=color)


def test_validate_project_with_long_name():
    name = "Project ab c de f gh i jk l mn pw r st u vw x yz ab c de f gh i jk l mn pw r st u vw x yz"
    color = 1
    with pytest.raises(
        ValidationError, match=r"String should have at most 80 characters"
    ):
        CreateProjectValidator(name=name, color=color)


def test_validate_project_with_long_description():
    name = "Project test"
    description = (
        "Project Lorem ipsum dolor sit amet, consectetuer adipiscing elit."
        "Aenean commodo ligula eget dolor. Aenean massa. Cum sociis natoque penatibus "
        "et magnis dis parturient montes, nascetur ridiculus mus. Donec quam fe "
        "aenean massa. Cum sociis natoque penatibus"
    )
    color = 1

    with pytest.raises(
        ValidationError, match=r"String should have at most 220 characters"
    ):
        CreateProjectValidator(name=name, description=description, color=color)


def test_validate_project_with_invalid_color():
    name = "Project test"
    color = 9

    with pytest.raises(
        ValidationError, match=r"Input should be less than or equal to 8"
    ):
        CreateProjectValidator(name=name, color=color)


def test_valid_project():
    name = "Project test"
    color = 1

    project = CreateProjectValidator(name=name, color=color)

    assert project.name == name
    assert project.color == color


def test_validate_logo_content_type():
    color = 1
    logo = f.build_string_uploadfile()

    with pytest.raises(ValidationError) as validations_errors:
        # noinspection PyArgumentList
        CreateProjectValidator(color=color, logo=logo)

    expected_error_fields = [
        "logo",
        "name",
    ]
    expected_error_messages = [
        "Value error, Invalid image content type",
        "Field required",
    ]
    check_validation_errors(
        validations_errors, expected_error_fields, expected_error_messages
    )


def test_validate_logo_content():
    color = 1
    logo = f.build_string_uploadfile(content_type="image/png")

    with pytest.raises(ValidationError) as validations_errors:
        # noinspection PyArgumentList
        CreateProjectValidator(color=color, logo=logo)

    expected_error_fields = ["logo", "name"]
    expected_error_messages = ["Value error, Invalid image content", "Field required"]
    check_validation_errors(
        validations_errors, expected_error_fields, expected_error_messages
    )


def test_validate_logo_name_empty():
    color = 1
    logo = ""

    with pytest.raises(ValidationError) as validations_errors:
        # noinspection PyArgumentList
        CreateProjectValidator(color=color, logo=logo)

    expected_error_fields = ["name"]
    expected_error_messages = ["Field required"]
    check_validation_errors(
        validations_errors, expected_error_fields, expected_error_messages
    )


##########################################################
# UpdateProjectValidator
##########################################################


def test_validate_update_project_ok():
    name = "new name"
    description = "new description"
    patch = UpdateProjectValidator(name=name, description=description)

    assert patch.name == name
    assert patch.description == description


def test_validate_update_project_ok_not_set():
    patch = UpdateProjectValidator()

    assert patch.name is None
    assert patch.description is None
    assert patch.model_dump(exclude_unset=True) == {}


def test_validate_update_project_ko_empty():
    name = ""
    description = None

    with pytest.raises(ValidationError) as validations_errors:
        # noinspection PyArgumentList
        UpdateProjectValidator(name=name, description=description)

    expected_error_fields = ["name", "description"]
    expected_error_messages = [
        "String should have at least 1 character",
        "Input should be a valid string",
    ]
    check_validation_errors(
        validations_errors, expected_error_fields, expected_error_messages
    )


def test_validate_update_project_ko_none():
    name = None

    with pytest.raises(ValidationError) as validations_errors:
        # noinspection PyArgumentList
        UpdateProjectValidator(name=name)

    expected_error_fields = ["name"]
    expected_error_messages = [
        "Input should be a valid string",
    ]
    check_validation_errors(
        validations_errors, expected_error_fields, expected_error_messages
    )
