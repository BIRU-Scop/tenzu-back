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

import json
from typing import Any
from unittest.mock import Mock

from pydantic import ValidationError


def check_validation_errors(
    validation_errors: ValidationError, error_fields: list[str], error_msgs: list[str]
):
    validation_errors_json = json.loads(validation_errors.value.json())
    assert len(validation_errors_json) == len(
        error_fields
    ), "Wrong number of validation errors"

    for error in validation_errors_json:
        if error["loc"][0] in error_fields:
            assert (
                error["msg"] in error_msgs
            ), f"'{error['msg']}' is not one of the expected errors {error_msgs}"


def preserve_real_attrs(mocked_object: Mock, real_object: Any, attr_names: list):
    """
    Set back the real attribute on a mock object
    """
    for attr_name in attr_names:
        real_attr = getattr(real_object, attr_name)
        setattr(
            mocked_object,
            attr_name,
            (lambda *args, **kwargs: real_attr(mocked_object, *args, **kwargs))
            if callable(real_attr)
            else real_attr,
        )
