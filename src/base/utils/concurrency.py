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

import asyncio
import functools
from collections.abc import Coroutine
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, TypeVar

import anyio

T = TypeVar("T")


def run_async_as_sync(coroutine: Coroutine[Any, Any, T]) -> T:
    pool = ThreadPoolExecutor(1)
    return pool.submit(asyncio.run, coroutine).result()


async def run_until_first_complete(*args: tuple[Callable[..., Any], dict[str, Any]]) -> None:
    async with anyio.create_task_group() as task_group:

        async def run(func: Callable[[], Coroutine[None, None, None]]) -> None:
            await func()
            task_group.cancel_scope.cancel()

        for func, kwargs in args:
            task_group.start_soon(run, functools.partial(func, **kwargs))
