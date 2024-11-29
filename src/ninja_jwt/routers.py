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

from ninja.router import Router

from ninja_jwt.schema_control import SchemaControl
from ninja_jwt.settings import api_settings

schema = SchemaControl(api_settings)

blacklist_router = Router()
obtain_pair_router = Router()
sliding_router = Router()
verify_router = Router()


@blacklist_router.post(
    "/blacklist",
    response={200: schema.blacklist_schema.get_response_schema()},
    url_name="token_blacklist",
    operation_id="token_blacklist",
    auth=None,
)
def blacklist_token(request, refresh: schema.blacklist_schema):
    return refresh.to_response_schema()


@obtain_pair_router.post(
    "/token",
    response=schema.obtain_pair_schema.get_response_schema(),
    url_name="token_obtain_pair",
    operation_id="token_obtain_pair",
    auth=None,
)
def obtain_token(request, user_token: schema.obtain_pair_schema):
    user_token.check_user_authentication_rule()
    return user_token.to_response_schema()


@obtain_pair_router.post(
    "/token/refresh",
    response=schema.obtain_pair_refresh_schema.get_response_schema(),
    url_name="token_refresh",
    operation_id="token_refresh",
    auth=None,
)
def refresh_token(request, refresh_token: schema.obtain_pair_refresh_schema):
    return refresh_token.to_response_schema()


@sliding_router.post(
    "/sliding",
    response=schema.obtain_sliding_schema.get_response_schema(),
    url_name="token_obtain_sliding",
    operation_id="token_obtain_sliding",
    auth=None,
)
def obtain_token_sliding_token(request, user_token: schema.obtain_sliding_schema):
    user_token.check_user_authentication_rule()
    return user_token.to_response_schema()


@sliding_router.post(
    "/sliding/refresh",
    response=schema.obtain_sliding_refresh_schema.get_response_schema(),
    url_name="token_refresh_sliding",
    operation_id="token_refresh_sliding",
    auth=None,
)
def refresh_token_sliding(request, refresh_token: schema.obtain_sliding_refresh_schema):
    return refresh_token.to_response_schema()


@verify_router.post(
    "/verify",
    response={200: schema.verify_schema.get_response_schema()},
    url_name="token_verify",
    operation_id="token_verify",
    auth=None,
)
def verify_token(request, token: schema.verify_schema):
    return token.to_response_schema()
