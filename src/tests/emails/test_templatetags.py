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
from datetime import timedelta

import pytest
from django.utils import translation

from commons.front.exceptions import InvalidFrontUrl
from emails.templatetags.email_extra import display_lifetime
from emails.templatetags.front_url import front_url


def test_front_url_success():
    relative_uri = "VERIFY_SIGNUP"
    verification_token = "ayJ0eXAiOiJKV1QaLCJhbGciOiJIUzI1fiJ9"

    url = front_url(url_key=relative_uri, verification_token=verification_token)

    assert (
        url
        == "http://localhost:4200/signup/verify/ayJ0eXAiOiJKV1QaLCJhbGciOiJIUzI1fiJ9"
    )


def test_front_url_error():
    relative_uri = "BAD_URI"
    verification_token = "ayJ0eXAiOiJKV1QaLCJhbGciOiJIUzI1fiJ9"

    with pytest.raises(InvalidFrontUrl):
        front_url(url_key=relative_uri, verification_token=verification_token)


def test_front_url_with_params():
    relative_uri = "VERIFY_SIGNUP"
    verification_token = "ayJ0eXAiOiJKV1QaLCJhbGciOiJIUzI1fiJ9"
    query_params = {"param1": "A", "param2": "B"}

    url = front_url(
        relative_uri, verification_token=verification_token, query_params=query_params
    )

    assert (
        url
        == "http://localhost:4200/signup/verify/ayJ0eXAiOiJKV1QaLCJhbGciOiJIUzI1fiJ9?param1=A&param2=B"
    )


def test_display_lifetime():
    with translation.override("en-US"):
        assert display_lifetime(timedelta(days=3)) == "3 days"

        assert display_lifetime(timedelta(days=1, hours=12)) == "1 day"

        assert display_lifetime(timedelta(days=1)) == "1 day"

        assert display_lifetime(timedelta(hours=12)) == "12 hours"

        assert display_lifetime(timedelta(hours=3, minutes=30)) == "3 hours"

        assert display_lifetime(timedelta(hours=1)) == "1 hour"

        assert display_lifetime(timedelta(minutes=45)) == "45 minutes"

        assert display_lifetime(timedelta(minutes=1)) == "1 minute"

        assert display_lifetime(timedelta(minutes=0)) == "0 minutes"
