# -*- coding: utf-8 -*-
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

import asyncio
import logging
import threading
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager, contextmanager

from django.conf import settings
from redis import Redis
from redis.asyncio import Redis as AsyncRedis
from redis.asyncio.lock import Lock as AsyncLock
from redis.exceptions import LockNotOwnedError
from redis.lock import Lock

logger = logging.getLogger(__name__)


def _no_configuration_redis_warning() -> None:
    logger.warning(
        "Please configure a redis in order to be able to use a lock. Without redis, the lock object won't do anything"
    )


##########################################################
# async
##########################################################


async def _akeep_alive(lock: AsyncLock, ttl: float) -> None:
    try:
        while True:
            await asyncio.sleep(ttl / 2)
            await lock.extend(ttl, replace_ttl=True)
    except asyncio.CancelledError:
        raise
    except LockNotOwnedError:
        logger.error("Redis lost the lock %r, perhaps after a reboot", lock.name)
    except Exception:
        logger.exception("Failed to extend redis lock %r", lock.name)


@asynccontextmanager
async def aget_redis_lock(
    key: str,
    blocking_timeout: float | None = None,
    ttl: float = 60,
) -> AsyncIterator[AsyncLock | None]:
    if settings.REDIS_URL is None:
        _no_configuration_redis_warning()
        yield None
        return

    async with AsyncRedis.from_url(settings.REDIS_URL) as client:
        lock = client.lock(
            key,
            timeout=ttl,
            blocking_timeout=blocking_timeout,
            thread_local=False,
        )
        async with lock:
            refresher = asyncio.create_task(_akeep_alive(lock, ttl))
            try:
                yield lock
            finally:
                refresher.cancel()


##########################################################
# sync
##########################################################


def _keep_alive(lock: Lock, ttl: float, stop: threading.Event) -> None:
    while not stop.wait(ttl / 2):
        try:
            lock.extend(ttl, replace_ttl=True)
        except LockNotOwnedError:
            logger.error("Redis lost the lock %r, perhaps after a reboot", lock.name)
            return
        except Exception:
            logger.exception("Failed to extend redis lock %r", lock.name)


@contextmanager
def get_redis_lock(
    key: str,
    blocking_timeout: float | None = None,
    ttl: float = 60,
) -> Iterator[Lock | None]:
    if settings.REDIS_URL is None:
        _no_configuration_redis_warning()
        yield None
        return

    with Redis.from_url(settings.REDIS_URL) as client:
        lock = client.lock(
            key,
            timeout=ttl,
            blocking_timeout=blocking_timeout,
            thread_local=False,
        )
        with lock:
            stop = threading.Event()
            refresher = threading.Thread(
                target=_keep_alive, args=(lock, ttl, stop), daemon=True
            )
            refresher.start()
            try:
                yield lock
            finally:
                stop.set()
                refresher.join()
