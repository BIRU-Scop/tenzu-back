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
from typing import Any, Callable, ContextManager

import pytest
from django.conf import settings


@pytest.fixture
def override_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[Callable[[dict[str, Any]], ContextManager[None]], None, None]:
    """
    Useful to overrided some settings values:

    This is a fixture that return a context manager, so you can use it like this:

        >>>
        async def test_example1(override_settings):
           ...
           with override_settings({"SECRET_KEY": "TEST_SECRET kEY"}):
              ...
           ...
    """

    @contextmanager
    def _override_settings(
        settings_values: dict[str, Any],
    ) -> Generator[None, None, None]:
        # Apply changes
        for attr, val in settings_values.items():
            monkeypatch.setattr(settings, attr, val)

        # Run the test
        yield

        # Undo changes
        monkeypatch.undo()

    yield _override_settings
