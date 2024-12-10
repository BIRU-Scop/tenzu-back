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

from datetime import datetime
from typing import Union

import pytest
from pydantic import ConfigDict

from base.mocks import (
    MAX_LIST_LENGTH,
    MAX_NESTED_INDEX,
    MIN_LIST_LENGTH,
    mock_serializer,
)
from base.serializers import BaseModel


class SimpleModel(BaseModel):
    text: str
    num: int
    boolean: bool
    date_hour: datetime
    dictionary: dict


class ListsModel(BaseModel):
    num_list: list[int]
    text_list: list[str]
    boolean_list: list[bool]
    datetime_list: list[datetime]
    dict_list: list[dict]
    simple_model_list: list[SimpleModel]


class NestedModel1(BaseModel):
    foo: Union["NestedModel2", None] = None
    bar: SimpleModel
    model_config = ConfigDict(from_attributes=False)


class NestedModel2(BaseModel):
    foo: Union["NestedModel3", None] = None
    bar: SimpleModel
    model_config = ConfigDict(from_attributes=False)


class NestedModel3(BaseModel):
    foo: Union["NestedModel1", None] = None
    bar: SimpleModel
    model_config = ConfigDict(from_attributes=False)


class OptionalModel(BaseModel):
    foo: SimpleModel | None = None
    bar: int
    model_config = ConfigDict(from_attributes=False)


NestedModel1.update_forward_refs()
NestedModel2.update_forward_refs()


def testing_simple_types():
    mocked_object = mock_serializer(SimpleModel)
    _validate_simple_model(mocked_object)


# TODO: fix _is_base_model_type in base/mocks
@pytest.mark.skip(reason="fix _is_base_model_type in base/mocks")
def testing_mocked_list_fields():
    mocked_object = mock_serializer(ListsModel)

    _validate_list(mocked_object.simple_model_list, SimpleModel)
    for simple_model in mocked_object.simple_model_list:
        _validate_simple_model(simple_model)


def testing_optional_field():
    mocked_object = mock_serializer(OptionalModel)

    _validate_optional(type(mocked_object.foo))


def testing_nested_cycling_properties():
    mocked_object = mock_serializer(NestedModel1)

    _validate_nested_cyclic(mocked_object.foo)
    _validate_simple_model(mocked_object.bar)


def testing_list_of_base_model():
    mocked_object_list = mock_serializer(list[SimpleModel])

    _validate_list(mocked_object_list, SimpleModel)


def _validate_simple_model(mocked_object):
    _validate_text(mocked_object.text)
    _validate_num(mocked_object.num)
    _validate_bool(mocked_object.boolean)
    _validate_dictionary(mocked_object.dictionary)
    _validate_datetime(mocked_object.date_hour)


def _validate_list(list_2_test: str, list_type: type):
    assert isinstance(list_2_test, list)
    assert len(list_2_test) >= MIN_LIST_LENGTH
    assert len(list_2_test) <= MAX_LIST_LENGTH
    for list_item in list_2_test:
        assert isinstance(list_item, list_type)


def _validate_optional(mocked_object):
    assert mocked_object == type(None) or mocked_object == SimpleModel  # noqa: E721


def _validate_nested_cyclic(mocked_object, nested_index: int = 0):
    if mocked_object is not None and nested_index <= MAX_NESTED_INDEX:
        assert nested_index <= MAX_NESTED_INDEX
        _validate_nested_cyclic(mocked_object.foo, nested_index + 1)


def _validate_text(text: str):
    assert isinstance(text, str)
    assert len(text) >= 1


def _validate_num(num: int):
    assert isinstance(num, int)
    assert num >= 0


def _validate_bool(boolean: bool):
    assert isinstance(boolean, bool)
    assert boolean in [True, False]


def _validate_datetime(date_hour: datetime):
    assert isinstance(date_hour, datetime)
    assert len(date_hour.__str__()) == 19


def _validate_dictionary(dictionary: datetime):
    assert isinstance(dictionary, dict)
    assert dictionary == dict()
