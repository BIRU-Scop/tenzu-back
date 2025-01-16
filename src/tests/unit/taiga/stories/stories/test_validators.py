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

from stories.stories.api.validators import ReorderStoriesValidator, ReorderValidator
from tests.utils.bad_params import NOT_EXISTING_B64ID

#######################################################
# ReorderValidator
#######################################################


async def test_reorder_validator_ok():
    assert ReorderValidator(place="after", ref=2)
    assert ReorderValidator(place="before", ref=2)


async def test_reorder_validator_fail():
    with pytest.raises(ValidationError) as exc_info:
        ReorderValidator(place="other", ref=2)
    assert exc_info.value.errors() == [
        {
            "loc": ("place",),
            "msg": "Place should be 'after' or 'before'",
            "type": "assertion_error",
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        ReorderValidator()
    assert exc_info.value.errors() == [
        {"loc": ("place",), "msg": "Field required", "type": "value_error.missing"},
        {"loc": ("ref",), "msg": "Field required", "type": "value_error.missing"},
    ]

    with pytest.raises(ValidationError) as exc_info:
        ReorderValidator(place="after", ref="str")
    assert exc_info.value.errors() == [
        {
            "loc": ("ref",),
            "msg": "value is not a valid integer",
            "type": "type_error.integer",
        }
    ]


#######################################################
# ReorderStoriesValidator
#######################################################


async def test_reorder_stories_validator_ok():
    reorder = ReorderValidator(place="after", ref=2)
    assert ReorderStoriesValidator(
        status=NOT_EXISTING_B64ID, stories=[1, 2, 3], reorder=reorder
    )
    assert ReorderStoriesValidator(status=NOT_EXISTING_B64ID, stories=[1, 2, 3])


async def test_reorder_stories_validator_fail():
    with pytest.raises(ValidationError) as exc_info:
        ReorderStoriesValidator(status=NOT_EXISTING_B64ID, stories=[])
    assert exc_info.value.errors() == [
        {
            "ctx": {"limit_value": 1},
            "loc": ("stories",),
            "msg": "ensure this value has at least 1 items",
            "type": "value_error.list.min_items",
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        ReorderStoriesValidator(status=None, stories=[1])
    assert exc_info.value.errors() == [
        {
            "loc": ("status",),
            "msg": "none is not an allowed value",
            "type": "type_error.none.not_allowed",
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        ReorderStoriesValidator(
            status=NOT_EXISTING_B64ID, stories=[1], reorder={"place": "nope", "ref": 3}
        )
    assert exc_info.value.errors() == [
        {
            "loc": ("reorder", "place"),
            "msg": "Place should be 'after' or 'before'",
            "type": "assertion_error",
        }
    ]
