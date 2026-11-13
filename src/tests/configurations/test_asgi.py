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
from collections.abc import Callable
from typing import Any

import pytest
from channels.testing import HttpCommunicator
from django.conf import settings
from django.db import connections

from configurations.asgi import application

FIRST_QUERY_TIMEOUT_SECONDS = 5
LATE_LOG_GRACE_SECONDS = 0.1
AUTH_CONFIG_PATH = f"/api/{settings.API_VERSION}/auth/config"


@pytest.mark.django_db
async def test_asgi_application_logs_nothing_above_info_when_the_client_disconnects(
    caplog,
):
    caplog.set_level(logging.INFO)
    communicator = HttpCommunicator(
        application, "GET", AUTH_CONFIG_PATH, headers=[(b"host", b"testserver")]
    )
    loop = asyncio.get_running_loop()
    first_query_executed = asyncio.Event()

    def on_execute(
        execute: Callable[..., Any],
        sql: str,
        params: Any,
        many: bool,
        context: dict[str, Any],
    ) -> Any:
        loop.call_soon_threadsafe(first_query_executed.set)
        return execute(sql, params, many, context)

    with connections["default"].execute_wrapper(on_execute):
        await communicator.send_input({"type": "http.request", "body": b""})
        await asyncio.wait_for(first_query_executed.wait(), FIRST_QUERY_TIMEOUT_SECONDS)
        await communicator.send_input({"type": "http.disconnect"})
        await communicator.wait()
    await asyncio.sleep(LATE_LOG_GRACE_SECONDS)

    assert [
        record.getMessage()
        for record in caplog.records
        if record.levelno > logging.INFO
    ] == []
