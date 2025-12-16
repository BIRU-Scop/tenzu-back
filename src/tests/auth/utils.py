# Copyright (C) 2025 BIRU
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

from urllib.parse import ParseResult, ParseResultBytes, parse_qs, urlparse

from django.conf import settings
from django.test import Client


def provider_auth(
    ssr_client: Client, post_data: dict, user_data: dict
) -> tuple[ParseResult | ParseResultBytes, dict]:
    response = ssr_client.post(
        f"/api/{settings.API_VERSION}/auth/provider/dummy/redirect", data=post_data
    )
    assert response.status_code == 302

    # request to provider's auth page
    response = ssr_client.get(response.url)
    assert response.status_code == 200

    # fill dummy provider form
    response = ssr_client.post(response.context_data["action_url"], data=user_data)

    # response provide redirection to callback url
    assert response.status_code == 302
    callback_url = urlparse(response.url)
    assert callback_url.path == post_data["callbackUrl"].split("?")[0]
    query = parse_qs(callback_url.query)
    return callback_url, query
