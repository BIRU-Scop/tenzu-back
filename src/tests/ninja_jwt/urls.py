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
from copy import deepcopy

# Copyright 2021 Ezeudoh Tochukwu
# https://github.com/eadwinCode/django-ninja-jwt
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
from django.urls import path
from ninja import NinjaAPI, Router

from ninja_jwt import authentication
from ninja_jwt.ninja_extra import exceptions
from ninja_jwt.routers import (
    blacklist_router,
    obtain_pair_router,
    sliding_router,
    verify_router,
)
from ninja_jwt.schema_control import SchemaControl
from ninja_jwt.settings import api_settings

schema = SchemaControl(api_settings)

# sync routes


sync_api = NinjaAPI(
    urls_namespace="jwt",
)


def api_exception_handler(request, exc):
    headers = {}

    if isinstance(exc.detail, (list, dict)):
        data = exc.detail
    else:
        data = {"detail": exc.detail}

    response = sync_api.create_response(request, data, status=exc.status_code)
    for k, v in headers.items():
        response.setdefault(k, v)

    return response


sync_api.exception_handler(exceptions.APIException)(api_exception_handler)

sync_router = Router()


def reset_router(router: Router) -> Router:
    router = deepcopy(router)
    router.api = None
    return router


sync_router.add_router("", reset_router(obtain_pair_router))
sync_router.add_router("", reset_router(sliding_router))
sync_router.add_router("", reset_router(verify_router))
sync_router.add_router("", reset_router(blacklist_router))

sync_api.add_router("", tags=["token"], router=sync_router, auth=None)


@sync_api.get("/test-view/test", url_name="test_view", auth=authentication.JWTAuth())
def test(request):
    return {"foo": "bar"}


# async routes

async_api = NinjaAPI(
    urls_namespace="jwt-async",
)
async_api.exception_handler(exceptions.APIException)(api_exception_handler)
async_router = Router()


@async_router.post(
    "/blacklist",
    response={200: schema.blacklist_schema.get_response_schema()},
    url_name="token_blacklist",
    operation_id="async_token_blacklist",
    auth=None,
)
async def ablacklist_token(request, refresh: schema.blacklist_schema):
    return refresh.to_response_schema()


@async_router.post(
    "/token",
    response=schema.obtain_pair_schema.get_response_schema(),
    url_name="token_obtain_pair",
    operation_id="async_token_obtain_pair",
    auth=None,
)
async def aobtain_token(request, user_token: schema.obtain_pair_schema):
    user_token.check_user_authentication_rule()
    return user_token.to_response_schema()


@async_router.post(
    "/token/refresh",
    response=schema.obtain_pair_refresh_schema.get_response_schema(),
    url_name="token_refresh",
    operation_id="async_token_refresh",
    auth=None,
)
async def arefresh_token(request, refresh_token: schema.obtain_pair_refresh_schema):
    return refresh_token.to_response_schema()


@async_router.post(
    "/sliding",
    response=schema.obtain_sliding_schema.get_response_schema(),
    url_name="token_obtain_sliding",
    operation_id="async_token_obtain_sliding",
    auth=None,
)
async def aobtain_token_sliding_token(
    request, user_token: schema.obtain_sliding_schema
):
    user_token.check_user_authentication_rule()
    return user_token.to_response_schema()


@async_router.post(
    "/sliding/refresh",
    response=schema.obtain_sliding_refresh_schema.get_response_schema(),
    url_name="token_refresh_sliding",
    operation_id="async_token_refresh_sliding",
    auth=None,
)
async def arefresh_token_sliding(
    request, refresh_token: schema.obtain_sliding_refresh_schema
):
    return refresh_token.to_response_schema()


@async_router.post(
    "/verify",
    response={200: schema.verify_schema.get_response_schema()},
    url_name="token_verify",
    operation_id="async_token_verify",
    auth=None,
)
async def averify_token(request, token: schema.verify_schema):
    return token.to_response_schema()


@async_api.get(
    "/test-view-async/test-async",
    url_name="test_view",
    auth=authentication.AsyncJWTAuth(),
)
async def atest(request):
    return {"foo": "bar"}


async_api.add_router(
    "",
    tags=["token-async"],
    router=async_router,
    auth=None,
)

urlpatterns = [
    path("api/", sync_api.urls),
    path("api/async/", async_api.urls),
]
