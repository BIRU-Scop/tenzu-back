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

# TODO(spade): redo with ninja api

# import pytest
# from fastapi import APIRouter
# from auth.routing import AuthAPIRouter
# from auth.tokens import AccessToken
# from base.api import Request
#
# from main import api
# from tests.utils import factories as f
# from tests.utils.testclient import TestClient
#
# pytestmark = pytest.mark.django_db
#
#
# def get_auth_info(request: Request):
#     try:
#         return {"user": request.user, "auth": request.auth}
#     except AssertionError:
#         return "no-auth"
#
#
# common_router: APIRouter = APIRouter(prefix="/tests")
# common_router.get("/not-authenticated-endpoint")(get_auth_info)
#
# auth_router: APIRouter = AuthAPIRouter(prefix="/tests")
# auth_router.get("/authenticated-endpoint")(get_auth_info)
#
# api.include_router(common_router)
# api.include_router(auth_router)
#
# client = TestClient(api)
#
#
# BASE_HEADERS = {
#     "Origin": "https://example.org",
# }
#
#
# #
# # Auth router
# #
#
#
# def test_auth_router_without_auth_token():
#     headers = BASE_HEADERS
#
#     response = client.get("/tests/authenticated-endpoint", headers=headers)
#     assert response.status_code == 200, response.text
#     assert "access-control-allow-origin" in response.headers.keys()
#     assert "access-control-allow-credentials" in response.headers.keys()
#     assert "auth" in response.json().keys()
#     assert "user" in response.json().keys()
#
#
# async def test_auth_router_with_valid_auth_token():
#     user = await f.create_user()
#     token = await sync_to_async(AccessToken.for_user)(user)
#     headers = BASE_HEADERS | {
#         "Authorization": f"Bearer {token}",
#     }
#
#     response = client.get("/tests/authenticated-endpoint", headers=headers)
#     assert response.status_code == 200, response.text
#     assert "access-control-allow-origin" in response.headers.keys()
#     assert "access-control-allow-credentials" in response.headers.keys()
#     assert "auth" in response.json().keys()
#     assert "user" in response.json().keys()
#
#
# def test_auth_router_with_invalid_auth_token():
#     headers = BASE_HEADERS | {
#         "Authorization": "Bearer invalid_token",
#     }
#
#     response = client.get("/tests/authenticated-endpoint", headers=headers)
#     assert response.status_code == 401, response.text
#     assert "access-control-allow-origin" in response.headers.keys()
#     assert "access-control-allow-credentials" in response.headers.keys()
#     assert "auth" not in response.json().keys()
#     assert "user" not in response.json().keys()
#
#
# #
# # Common router
# #
#
#
# def test_router_without_auth_token():
#     headers = BASE_HEADERS
#
#     response = client.get("/tests/not-authenticated-endpoint", headers=headers)
#     assert response.status_code == 200, response.text
#     assert "access-control-allow-origin" in response.headers.keys()
#     assert "access-control-allow-credentials" in response.headers.keys()
#     assert "no-auth" in response.json()
#
#
# async def test_router_with_valid_auth_token():
#     user = await f.create_user()
#     token = await sync_to_async(AccessToken.for_user)(user)
#     headers = BASE_HEADERS | {
#         "Authorization": f"Bearer {token}",
#     }
#
#     response = client.get("/tests/not-authenticated-endpoint", headers=headers)
#     assert response.status_code == 200, response.text
#     assert "access-control-allow-origin" in response.headers.keys()
#     assert "access-control-allow-credentials" in response.headers.keys()
#     assert "no-auth" in response.json()
#
#
# def test_router_with_invalid_auth_token():
#     headers = BASE_HEADERS | {
#         "Authorization": "Bearer invalid_token",
#     }
#
#     response = client.get("/tests/not-authenticated-endpoint", headers=headers)
#     assert response.status_code == 200, response.text
#     assert "access-control-allow-origin" in response.headers.keys()
#     assert "access-control-allow-credentials" in response.headers.keys()
#     assert "no-auth" in response.json()
