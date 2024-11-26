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

from base import templating
from base.templating import get_environment


@pytest.fixture
def initialize_template_env(
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[Callable[[], ContextManager[None]], None, None]:
    """
    Useful to work with an "new" and "clean" Enviroment object at `tenzu.base.templating.env`.

    This is a fixture that return context manager, so you can use it like this:

        >>>
        async def test_example1(initialize_template_env):
           ...
           with initialize_template_env():
              ...
           ...
    """

    @contextmanager
    def _initialize_templating_env() -> Generator[None, None, None]:
        # Apply changes
        new_env = get_environment()
        monkeypatch.setattr(templating, "env", new_env)

        # Run the test
        yield

        # Undo changes
        monkeypatch.undo()

    yield _initialize_templating_env
