# -*- coding: utf-8 -*-
# Copyright (C) 2024-2025 BIRU
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

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from commons.exceptions.api import UnexpectedExceptionMiddleware
from tests.utils.testclient import TestClient

CORS_ATTRS = {
    "allow_origins": ["*"],
    "allow_credentials": True,
    "allow_methods": ["*"],
    "allow_headers": ["*"],
}

app = FastAPI()
app.add_middleware(UnexpectedExceptionMiddleware)
app.add_middleware(CORSMiddleware, **CORS_ATTRS)


@app.get("/success")
def get_successok():
    return {}


@app.get("/error")
def get_error():
    1 / 0
    return {}


client = TestClient(app)


def test_there_is_no_error():
    response = client.get("/success")
    assert response.status_code == 200, response.text
    assert response.data == {}


def test_500_errors_has_cors_headers_with_origin_in_request(caplog):
    with caplog.at_level(logging.CRITICAL, logger="exceptions.api.middlewares"):
        response = client.get("/error", headers={"Origin": "http://example.com"})

    assert response.status_code == 500, response.text
    assert "access-control-allow-origin" in response.headers
    assert "access-control-allow-credentials" in response.headers

    error = response.data["error"]
    assert "code" in error
    assert "detail" in error and isinstance(error["detail"], str)
    assert "msg" in error


def test_500_errors_has_not_cors_headers_without_origin_in_request(caplog):
    with caplog.at_level(logging.CRITICAL, logger="exceptions.api.middlewares"):
        response = client.get("/error")

    assert response.status_code == 500, response.text
    assert "access-control-allow-origin" not in response.headers
    assert "access-control-allow-credentials" not in response.headers

    error = response.data["error"]
    assert "code" in error
    assert "detail" in error and isinstance(error["detail"], str)
    assert "msg" in error
