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

from fastapi import FastAPI, Security
from fastapi.security import HTTPAuthorizationCredentials

from auth.security import HTTPBearer
from tests.utils.testclient import TestClient

app = FastAPI()
client = TestClient(app)


# auto_error = True


@app.get("/credentials")
def get_credentials(
    credentials: HTTPAuthorizationCredentials | None = Security(HTTPBearer()),
):
    return {"scheme": credentials.scheme, "credentials": credentials.credentials} if credentials else {}


def test_security_http_bearer_success_no_credentials():
    response = client.get("/credentials")
    assert response.status_code == 200, response.text
    assert response.json() == {}


def test_security_http_bearer_success_with_credentials():
    response = client.get("/credentials", headers={"Authorization": "Bearer foobar"})
    assert response.status_code == 200, response.text
    assert response.json() == {"scheme": "bearer", "credentials": "foobar"}


def test_security_http_bearer_error_incorrect_scheme_credentials():
    response = client.get("/credentials/", headers={"Authorization": "Basic notreally"})
    assert response.status_code == 401, response.text


# auto_error = False


@app.get("/credentials-no-auto-error")
def get_credentials_no_error(
    credentials: HTTPAuthorizationCredentials | None = Security(HTTPBearer(auto_error=False)),
):
    return {"scheme": credentials.scheme, "credentials": credentials.credentials} if credentials else {}


def test_security_http_bearer_success_no_auto_error():
    response = client.get("/credentials-no-auto-error/", headers={"Authorization": "Basic notreally"})
    assert response.status_code == 200, response.text
    assert response.json() == {}
