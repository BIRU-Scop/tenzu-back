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
import gc
from dataclasses import dataclass
from typing import Self
from unittest.mock import MagicMock, patch

import pytest

from tasksqueue.middleware import collect_garbage_after_job


def _context():
    context = MagicMock()
    context.job.id = 42
    context.job.task_name = "test.task"
    return context


async def test_collect_garbage_after_job_returns_result_and_collects():
    async def call_next():
        return "result"

    with patch.object(gc, "collect", return_value=3) as collect:
        result = await collect_garbage_after_job(call_next, _context(), MagicMock())

    assert result == "result"
    assert collect.call_args_list == [(), ()]


async def test_collect_garbage_after_job_collects_even_when_job_fails():
    async def call_next():
        raise RuntimeError("error")

    with patch.object(gc, "collect", return_value=0) as collect:
        with pytest.raises(RuntimeError):
            await collect_garbage_after_job(call_next, _context(), MagicMock())

    assert collect.call_args_list == [(), ()]


async def test_collect_garbage_after_job_frees_a_reference_cycle():
    @dataclass
    class Node:
        node: Self | None = None

    gc.collect()

    async def call_next():
        a, b = Node(), Node()
        a.node, b.node = b, a

    await collect_garbage_after_job(call_next, _context(), MagicMock())

    assert not any(isinstance(object, Node) for object in gc.get_objects())
