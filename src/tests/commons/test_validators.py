# Copyright (C) 2024-2026 BIRU
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

from uuid import uuid1

import pytest
from pydantic import ValidationError

from base.utils.uuid import encode_uuid_to_b64str
from commons.validators import B64UUID, BaseModel, LanguageCode, StrNotEmpty

#########################################################
# LanguageCode
#########################################################


class LanguageCodeModel(BaseModel):
    x: LanguageCode


def test_language_code_with_valid_value():
    m = LanguageCodeModel(x="en-us")

    assert m.x == "en-us"


@pytest.mark.parametrize(
    "value",
    ["invalid", "en_us", "", None],
)
def test_language_code_with_invalid_value(value):
    with pytest.raises(ValidationError):
        LanguageCodeModel(x=value)


#########################################################
# StrNotEmpty
#########################################################


class StrNotEmptyModel(BaseModel):
    x: StrNotEmpty


def test_str_not_empty_with_valid_value():
    assert StrNotEmptyModel(x="a").x == "a"


@pytest.mark.parametrize(
    "value",
    ["", "   ", None],
)
def test_str_not_empty_with_invalid_value(value):
    with pytest.raises(ValidationError):
        StrNotEmptyModel(x=value)


#########################################################
# B64UUID
#########################################################


class B64UUIDModel(BaseModel):
    x: B64UUID


def test_b64uuid_with_valid_value():
    uuid = uuid1()

    m = B64UUIDModel(x=encode_uuid_to_b64str(uuid))

    assert m.x == uuid


@pytest.mark.parametrize(
    "value",
    ["invalid", "AAAshort", "AAAAAAAAAAAAAAAAAAAAAAAAlong", "", None],
)
def test_b64uuid_with_invalid_value(value):
    with pytest.raises(ValidationError):
        B64UUIDModel(x=value)
