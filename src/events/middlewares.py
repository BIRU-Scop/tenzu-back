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

from typing import ClassVar, Protocol
from uuid import uuid4

from asgiref.sync import iscoroutinefunction, markcoroutinefunction

from events.context import correlation_id


class Generator(Protocol):
    def __call__(self) -> str:
        pass


class AsyncCorrelationIdMiddleware:
    """
    Middleware for reading or generating correlation IDs for each incoming request. Correlation IDs can then be
    added to the log traces, making it simple to retrieve all logs generated from a single HTTP request.

    When the middleware detects a correlation ID HTTP header in an incoming request, the ID is stored. If no header
    is found, a correlation ID (an UUID v4) is generated for the request instead.

    This middleware checks for the 'Correlation-ID' header by default.

    NOTE:
      [1] Remember to add "Correlation-ID" to 'allow_headers' and 'expose_headers' at the CORSMiddleware.

    This middleware is inspired by
      - https://github.com/snok/asgi-correlation-id
      - https://github.com/tomwojcik/starlette-context
    """

    CORRELATION_ID_HEADER_NAME: ClassVar = "correlation-id"
    _generator: Generator
    async_capable = True
    sync_capable = False

    def __init__(self, get_response, generator: Generator = lambda: uuid4().hex):
        self.get_response = get_response
        self._generator = generator
        if iscoroutinefunction(self.get_response):
            markcoroutinefunction(self)

    async def __call__(self, request):
        """
        Load request ID from headers if present. Generate one otherwise.
        """
        # Try to load correlation ID from the request headers or generate a new ID if none was found
        id_value = (
            request.headers.get(self.CORRELATION_ID_HEADER_NAME.lower())
            or self._generator()
        )

        token = correlation_id.set(id_value)

        response = await self.get_response(request)
        response.headers[self.CORRELATION_ID_HEADER_NAME] = id_value

        correlation_id.reset(token)

        return response
