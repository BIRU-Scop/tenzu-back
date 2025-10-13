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


from datetime import timedelta

import pytest
from asgiref.sync import sync_to_async
from django.urls import reverse

from ninja_jwt.ninja_extra.lazy import LazyStrImport
from ninja_jwt.settings import api_settings
from ninja_jwt.tokens import AccessToken
from users.models import User

from ..utils.factories import sync_create_user as create_user
from .utils import APIViewTestCase


@pytest.mark.django_db
class TestTestView(APIViewTestCase):
    namespace = "jwt"

    @property
    def view_name(self):
        return f"{self.namespace}:test_view"

    @pytest.fixture(autouse=True)
    def setUp(self):
        super().setUp()
        self.username = "test_user"
        self.password = "test_password"

        self.user = create_user(
            username=self.username,
            password=self.password,
        )

    def test_no_authorization(self):
        res = self.view_get()

        assert res.status_code == 401
        assert "Unauthorized" in res.data["detail"]

    def test_wrong_auth_type(self):
        res = self.view_post(
            url=reverse(f"{self.namespace}:token_obtain_sliding"),
            data={
                User.USERNAME_FIELD: self.username,
                "password": self.password,
            },
            content_type="application/json",
        )

        token = res.data["token"]
        self.authenticate_with_token("Wrong", token)

        res = self.view_get()

        assert res.status_code == 401
        assert "Unauthorized" in res.data["detail"]

    def test_expired_token(self, monkeypatch):
        old_lifetime = AccessToken.lifetime
        AccessToken.lifetime = timedelta(seconds=0)
        try:
            res = self.view_post(
                url=reverse(f"{self.namespace}:token_obtain_pair"),
                data={
                    User.USERNAME_FIELD: self.username,
                    "password": self.password,
                },
                content_type="application/json",
            )
        finally:
            AccessToken.lifetime = old_lifetime

        access = res.data["access"]
        self.authenticate_with_token("Bearer", access)

        with monkeypatch.context() as m:
            m.setattr(
                api_settings,
                "AUTH_TOKEN_CLASSES",
                (LazyStrImport("ninja_jwt.tokens.AccessToken"),),
            )
            res = self.view_get()

        assert res.status_code == 401
        assert "token_not_valid" == res.data["code"]

    def test_user_can_get_sliding_token_and_use_it(self, monkeypatch):
        res = self.view_post(
            url=reverse(f"{self.namespace}:token_obtain_sliding"),
            data={
                User.USERNAME_FIELD: self.username,
                "password": self.password,
            },
            content_type="application/json",
        )

        token = res.data["token"]
        self.authenticate_with_token("Bearer", token)

        with monkeypatch.context() as m:
            m.setattr(
                api_settings,
                "AUTH_TOKEN_CLASSES",
                (LazyStrImport("ninja_jwt.tokens.SlidingToken"),),
            )
            res = self.view_get()

        assert res.status_code == 200
        assert res.data["foo"] == "bar"

    def test_user_can_get_access_and_refresh_tokens_and_use_them(self, monkeypatch):
        res = self.view_post(
            url=reverse(f"{self.namespace}:token_obtain_pair"),
            data={
                User.USERNAME_FIELD: self.username,
                "password": self.password,
            },
            content_type="application/json",
        )

        access = res.data["access"]
        refresh = res.data["refresh"]

        self.authenticate_with_token("Bearer", access)

        with monkeypatch.context() as m:
            m.setattr(
                api_settings,
                "AUTH_TOKEN_CLASSES",
                (LazyStrImport("ninja_jwt.tokens.AccessToken"),),
            )
            res = self.view_get()

        assert res.status_code == 200
        assert res.data["foo"] == "bar"

        res = self.view_post(
            url=reverse(f"{self.namespace}:token_refresh"),
            data={"refresh": refresh},
            content_type="application/json",
        )

        access = res.data["access"]

        self.authenticate_with_token("Bearer", access)

        with monkeypatch.context() as m:
            m.setattr(
                api_settings,
                "AUTH_TOKEN_CLASSES",
                (LazyStrImport("ninja_jwt.tokens.AccessToken"),),
            )
            res = self.view_get()

        assert res.status_code == 200
        assert res.data["foo"] == "bar"


@pytest.mark.usefixtures("allow_async_unsafe")
class TestAsyncTestView(TestTestView):
    namespace = "jwt-async"

    @pytest.mark.django_db(transaction=True)
    async def test_no_authorization(self):
        _test_no_authorization = sync_to_async(super().test_no_authorization)
        await _test_no_authorization()

    @pytest.mark.django_db(transaction=True)
    async def test_wrong_auth_type(self):
        _test_wrong_auth_type = sync_to_async(super().test_wrong_auth_type)
        await _test_wrong_auth_type()

    @pytest.mark.django_db(transaction=True)
    async def test_expired_token(self, monkeypatch):
        _test_expired_token = sync_to_async(super().test_expired_token)
        await _test_expired_token(monkeypatch=monkeypatch)

    @pytest.mark.django_db(transaction=True)
    async def test_user_can_get_sliding_token_and_use_it(self, monkeypatch):
        _test_user_can_get_sliding_token_and_use_it = sync_to_async(
            super().test_user_can_get_sliding_token_and_use_it
        )
        await _test_user_can_get_sliding_token_and_use_it(monkeypatch=monkeypatch)

    @pytest.mark.django_db(transaction=True)
    async def test_user_can_get_access_and_refresh_tokens_and_use_them(
        self, monkeypatch
    ):
        _test_user_can_get_access_and_refresh_tokens_and_use_them = sync_to_async(
            super().test_user_can_get_access_and_refresh_tokens_and_use_them
        )
        await _test_user_can_get_access_and_refresh_tokens_and_use_them(
            monkeypatch=monkeypatch
        )
