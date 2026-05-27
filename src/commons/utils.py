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

import functools
from asyncio import Task, create_task
from functools import partial
from urllib.parse import urljoin

from asgiref.sync import async_to_sync, iscoroutinefunction, sync_to_async
from django.conf import settings
from django.db import transaction
from pydantic_core import Url


def get_absolute_url(url: str | Url):
    if str(url).startswith("/"):
        # relative url
        return urljoin(str(settings.BACKEND_URL), url)
    return url


def transaction_atomic_async(func):
    @sync_to_async
    def wrapper(*args, **kwargs):
        with transaction.atomic():
            return async_to_sync(func)(*args, **kwargs)

    return wrapper


def transaction_on_commit_async(func):
    @sync_to_async
    def wrapper(*args, **kwargs):
        sync_func = async_to_sync(func) if iscoroutinefunction(func) else func
        transaction.on_commit(partial(sync_func, *args, **kwargs))

    return wrapper


def async_cache(async_function):
    """
    Decorator to use functools.cache with async function
    !!!
    autospec won't work with patch in tests, should be called instead with:
        patch("PATH.FUNCTION_NAME", new=AsyncMock())
    """

    def clear_cache_on_exception(future: Task):
        try:
            future.result()
        except Exception as e:
            # prevent exception from being cached, to reproduce behaviour from functools.cache
            cached_async_function.cache_clear()

    @functools.cache
    def cached_async_function(*args, **kwargs) -> Task:
        coroutine = async_function(*args, **kwargs)
        future = create_task(coroutine)
        future.add_done_callback(clear_cache_on_exception)
        return future

    return cached_async_function
