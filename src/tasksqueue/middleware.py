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
import ctypes
import gc
import logging

logger = logging.getLogger(__name__)


def _load_malloc_trim():
    try:
        return ctypes.CDLL(None).malloc_trim
    except (OSError, AttributeError):
        return None


_malloc_trim = _load_malloc_trim()


def release_memory():
    gc.collect()
    if _malloc_trim is not None:
        _malloc_trim(0)


async def collect_garbage_after_job(call_next, context, worker):
    release_memory()
    try:
        return await call_next()
    finally:
        release_memory()
