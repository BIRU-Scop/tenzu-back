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
from humps import camelize, decamelize

from base.api.ordering import OrderQuery
from exceptions.api import ValidationError


def test_validate_ordering_valid_params(client):
    allowed_field_list = ["created_at", "-created_at", "text", "-text"]
    default_ordering_list = ["-created_at"]
    ordering_query = OrderQuery(
        allowed=allowed_field_list, default=default_ordering_list
    )

    valid_field_list = ["-createdAt", "text"]
    result = ordering_query.__call__(order=valid_field_list)

    assert result == list(map(decamelize, valid_field_list))


def test_validate_ordering_invalid_params(client):
    allowed_field_list = ["created_at", "-created_at", "text", "-text"]
    default_ordering_list = ["-created_at"]
    ordering_query = OrderQuery(
        allowed=allowed_field_list, default=default_ordering_list
    )

    invalid_field = "invalid_field"
    ordering_params = allowed_field_list + [invalid_field]

    with pytest.raises(
        ValidationError, match=f"Invalid ordering fields: {camelize(invalid_field)}"
    ):
        ordering_query.__call__(order=ordering_params)
