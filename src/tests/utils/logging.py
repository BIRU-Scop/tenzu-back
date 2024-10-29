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

from collections.abc import Generator
from contextlib import contextmanager
from typing import Callable, ContextManager

import pytest

from base.logging import context


@pytest.fixture
def correlation_id() -> Generator[Callable[[str], ContextManager[None]], None, None]:
    """
    Useful to set correlation-id values:

    This is a fixture that return a context manager, so you can use it like this:

        >>>
        async def test_example1(correlation_id):
           ...
           with correlation_id("id-value"):
              ...
           ...
    """

    @contextmanager
    def _correlation_id(value: str) -> Generator[None, None, None]:
        try:
            # Set the value
            token = context.correlation_id.set(value)
            # Run the test
            yield
        finally:
            # Reset the value
            context.correlation_id.reset(token)

    yield _correlation_id
