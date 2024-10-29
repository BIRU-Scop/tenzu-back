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

from tests.unit.utils import check_validation_errors
from users.api.validators import CreateUserValidator, UpdateUserValidator

###############################################
# CreateUserValidator
###############################################


def test_validate_create_user_ok_all_fields():
    email = "user@email.com"
    full_name = "User fullname"
    password = "Dragon123"
    terms = True
    project_inv_token = "eyJ0zB26LvR9jQw7"
    accept_project_invitation = False
    lang = "es-ES"

    validator = CreateUserValidator(
        email=email,
        full_name=full_name,
        password=password,
        accept_terms=terms,
        project_invitation_token=project_inv_token,
        accept_project_invitation=accept_project_invitation,
        lang=lang,
    )

    assert validator.email == email
    assert validator.full_name == full_name
    assert validator.password == password
    assert validator.accept_terms == terms
    assert validator.project_invitation_token == project_inv_token
    assert validator.accept_project_invitation == accept_project_invitation
    assert validator.lang == lang


def test_validate_create_user_wrong_not_all_required_fields():
    with pytest.raises(ValidationError) as validation_errors:
        CreateUserValidator()

    expected_error_fields = ["email", "password", "fullName", "acceptTerms"]
    expected_error_messages = ["field required"]
    check_validation_errors(validation_errors, expected_error_fields, expected_error_messages)


def test_validate_create_user_not_accepted_terms():
    email = "user@email.com"
    full_name = "User fullname"
    password = "Dragon123"
    terms = False

    with pytest.raises(ValidationError) as validation_errors:
        CreateUserValidator(email=email, full_name=full_name, password=password, accept_terms=terms)

    expected_error_fields = ["acceptTerms"]
    expected_error_messages = ["User has to accept terms of service"]
    check_validation_errors(validation_errors, expected_error_fields, expected_error_messages)


@pytest.mark.parametrize(
    "email",
    [
        "noAtnoDomain" "not.at.domain",
        "email@domain",
    ],
)
def test_validate_create_user_invalid_email(email):
    email = email
    full_name = "User fullname"
    password = "Dragon123"
    terms = True

    with pytest.raises(ValidationError) as validation_errors:
        CreateUserValidator(email=email, full_name=full_name, password=password, accept_terms=terms)

    expected_error_fields = ["email"]
    expected_error_messages = ["value is not a valid email address"]
    check_validation_errors(validation_errors, expected_error_fields, expected_error_messages)


@pytest.mark.parametrize(
    "password, error",
    [
        ("UPPERAndLower", "Invalid password"),
        ("UPPERANDNUMBER0", "Invalid password"),
        ("lowerandnumber0", "Invalid password"),
        ("&/()@+01234", "Invalid password"),
        ("symbol+andlower", "Invalid password"),
        ("SHORT", "ensure this value has at least 8 characters"),
    ],
)
def test_validate_create_user_invalid_password(password, error):
    email = "user@email.com"
    full_name = "User fullname"
    terms = True

    with pytest.raises(ValidationError) as validation_errors:
        CreateUserValidator(email=email, full_name=full_name, password=password, accept_terms=terms)

    check_validation_errors(validation_errors, ["password"], [error])


@pytest.mark.parametrize(
    "color, error",
    [
        (0, "ensure this value is greater than 0"),
        (9, "ensure this value is less than 9"),
        (-1, "ensure this value is greater than 0"),
    ],
)
def test_validate_create_user_invalid_color(color, error):
    email = "user@email.com"
    full_name = "User fullname"
    password = "Dragon123"
    terms = True

    with pytest.raises(ValidationError) as validation_errors:
        CreateUserValidator(
            email=email,
            full_name=full_name,
            color=color,
            password=password,
            accept_terms=terms,
        )

    check_validation_errors(validation_errors, ["color"], [error])


###############################################
# UpdateUserValidator
###############################################


def test_validate_update_user_ok_all_fields():
    full_name = "User fullname"
    lang = "es-ES"

    validator = UpdateUserValidator(
        full_name=full_name,
        lang=lang,
    )

    assert validator.full_name == full_name
    assert validator.lang == lang


def test_validate_update_user_wrong_not_all_required_fields():
    with pytest.raises(ValidationError) as validation_errors:
        UpdateUserValidator()

    expected_error_fields = ["fullName", "lang"]
    expected_error_messages = ["field required"]
    check_validation_errors(validation_errors, expected_error_fields, expected_error_messages)


@pytest.mark.parametrize(
    "lang",
    [
        "invalid",
        "es_ES",
    ],
)
def test_validate_update_user_invalid_language(lang):
    with pytest.raises(ValidationError) as validation_errors:
        UpdateUserValidator(
            full_name="new full name",
            lang=lang,
        )

    check_validation_errors(validation_errors, ["lang"], ["Language is not available"])
