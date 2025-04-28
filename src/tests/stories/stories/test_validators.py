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
from tests.utils.utils import check_validation_errors

#######################################################
# ReorderValidator
#######################################################


async def test_reorder_validator_ok():
    assert ReorderValidator(place="after", ref=2)
    assert ReorderValidator(place="before", ref=2)


async def test_reorder_validator_fail():
    with pytest.raises(ValidationError) as exc_info:
        ReorderValidator(place="other", ref=2)

    expected_error_fields = ["place"]
    expected_error_messages = ["Input should be 'before' or 'after'"]
    check_validation_errors(exc_info, expected_error_fields, expected_error_messages)

    with pytest.raises(ValidationError) as exc_info:
        # noinspection PyArgumentList
        ReorderValidator()
    expected_error_fields = ["place", "ref"]
    expected_error_messages = ["Field required"] * 2
    check_validation_errors(exc_info, expected_error_fields, expected_error_messages)

    with pytest.raises(ValidationError) as exc_info:
        ReorderValidator(place="after", ref="str")
    expected_error_fields = ["ref"]
    expected_error_messages = [
        "Input should be a valid integer, unable to parse string as an integer"
    ]
    check_validation_errors(exc_info, expected_error_fields, expected_error_messages)


#######################################################
# ReorderStoriesValidator
#######################################################


async def test_reorder_stories_validator_ok():
    reorder = ReorderValidator(place="after", ref=2)
    assert ReorderStoriesValidator(
        status_id=NOT_EXISTING_B64ID,
        stories=[1, 2, 3],
        reorder=reorder,
        workflow_slug="main",
    )
    assert ReorderStoriesValidator(
        status_id=NOT_EXISTING_B64ID, stories=[1, 2, 3], workflow_slug="main"
    )


async def test_reorder_stories_validator_fail():
    with pytest.raises(ValidationError) as exc_info:
        ReorderStoriesValidator(
            status_id=NOT_EXISTING_B64ID, stories=[], workflow_slug="main"
        )
    expected_error_fields = ["stories"]
    expected_error_messages = [
        "List should have at least 1 item after validation, not 0"
    ]
    check_validation_errors(exc_info, expected_error_fields, expected_error_messages)

    with pytest.raises(ValidationError) as exc_info:
        ReorderStoriesValidator(status_id=None, stories=[1], workflow_slug="main")
    expected_error_fields = ["status_id"]
    expected_error_messages = ["Input should be a valid string"]
    check_validation_errors(exc_info, expected_error_fields, expected_error_messages)

    with pytest.raises(ValidationError) as exc_info:
        ReorderStoriesValidator(
            status_id=NOT_EXISTING_B64ID,
            stories=[1],
            reorder={"place": "nope", "ref": 3},
            workflow_slug="main",
        )
    expected_error_fields = ["place"]
    expected_error_messages = ["Input should be 'before' or 'after'"]
    check_validation_errors(exc_info, expected_error_fields, expected_error_messages)
