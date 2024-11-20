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

from fastapi import FastAPI

from events.middlewares import CorrelationIdMiddleware
from tests.utils.testclient import TestClient

app = FastAPI()
app.add_middleware(CorrelationIdMiddleware)


@app.get("/success")
def get_successok():
    return {}


client = TestClient(app)


def test_request_without_correlation_id():
    response = client.get("/success")
    assert response.status_code == 200, response.text
    assert response.headers.get("correlation-id", None)


def test_request_with_correlation_id():
    correlation_id = "test-id"
    response = client.get("/success", headers={"correlation-id": correlation_id})
    assert response.status_code == 200, response.text
    assert response.headers.get("correlation-id", None) == correlation_id
