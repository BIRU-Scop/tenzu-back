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

from ninja_jwt import authentication
from ninja_jwt.exceptions import AuthenticationFailed, InvalidToken
from ninja_jwt.models import TokenUser
from ninja_jwt.settings import api_settings
from ninja_jwt.tokens import AccessToken, SlidingToken
from tests.utils.factories import sync_create_user as create_user

AuthToken = api_settings.AUTH_TOKEN_CLASSES[0]


class TestJWTAuth:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.init_backend()

    def init_backend(self):
        self.backend = authentication.JWTAuth()

    @pytest.mark.django_db
    def test_get_validated_token(self, monkeypatch):
        # Should raise InvalidToken if token not valid
        token = AuthToken()
        token.set_exp(lifetime=-timedelta(days=1))
        with pytest.raises(InvalidToken):
            self.backend.get_validated_token(str(token))

        # Otherwise, should return validated token
        token.set_exp()
        assert self.backend.get_validated_token(str(token)).payload == token.payload

        # Should not accept tokens not included in AUTH_TOKEN_CLASSES
        sliding_token = SlidingToken()
        with monkeypatch.context() as m:
            m.setattr(
                api_settings, "AUTH_TOKEN_CLASSES", ("ninja_jwt.tokens.AccessToken",)
            )
            with pytest.raises(InvalidToken) as e:
                self.backend.get_validated_token(str(sliding_token))

            details = e.value.detail
            assert len(details["messages"]) == 1
            assert details["messages"][0] == {
                "token_class": "AccessToken",
                "token_type": "access",
                "message": "Token has wrong type",
            }

        # Should accept tokens included in AUTH_TOKEN_CLASSES
        access_token = AccessToken()
        sliding_token = SlidingToken()
        with monkeypatch.context() as m:
            m.setattr(
                api_settings,
                "AUTH_TOKEN_CLASSES",
                (
                    "ninja_jwt.tokens.AccessToken",
                    "ninja_jwt.tokens.SlidingToken",
                ),
            )
            self.backend.get_validated_token(str(access_token))
            self.backend.get_validated_token(str(sliding_token))

    @pytest.mark.django_db
    def test_get_user(self):
        payload = {"some_other_id": "foo"}

        # Should raise error if no recognizable user identification
        with pytest.raises(InvalidToken):
            self.backend.get_user(payload)

        payload[api_settings.USER_ID_CLAIM] = 42

        # Should raise exception if user not found
        with pytest.raises(AuthenticationFailed):
            self.backend.get_user(payload)

        u = create_user(username="markhamill")
        u.is_active = False
        u.save()

        payload[api_settings.USER_ID_CLAIM] = getattr(u, api_settings.USER_ID_FIELD)

        # Should raise exception if user is inactive
        with pytest.raises(AuthenticationFailed):
            self.backend.get_user(payload)

        u.is_active = True
        u.save()

        # Otherwise, should return correct user
        assert self.backend.get_user(payload).id == u.id


class TestJWTTokenUserAuth:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.init_backend()

    def init_backend(self):
        self.backend = authentication.JWTTokenUserAuth()

    @pytest.mark.django_db
    def test_get_user(self):
        payload = {"some_other_id": "foo"}

        # Should raise error if no recognizable user identification
        with pytest.raises(InvalidToken):
            self.backend.get_user(payload)

        payload[api_settings.USER_ID_CLAIM] = 42

        # Otherwise, should return a token user object
        user = self.backend.get_user(payload)

        assert isinstance(user, TokenUser)
        assert user.id == 42

    @pytest.mark.django_db
    def test_custom_tokenuser(self, monkeypatch):
        from django.utils.functional import cached_property

        class BobSaget(TokenUser):
            @cached_property
            def username(self):
                return "bsaget"

        with monkeypatch.context() as m:
            m.setattr(api_settings, "TOKEN_USER_CLASS", BobSaget)

            # Should return a token user object
            payload = {api_settings.USER_ID_CLAIM: 42}
            user = self.backend.get_user(payload)

            assert isinstance(user, api_settings.TOKEN_USER_CLASS)
            assert user.id == 42
            assert user.username == "bsaget"


class TestAsyncJWTAuth(TestJWTAuth):
    def init_backend(self):
        self.backend = authentication.AsyncJWTAuth()

    @pytest.mark.django_db
    async def test_get_validated_token(self, monkeypatch):
        _test_get_validated_token = sync_to_async(
            super(TestAsyncJWTAuth, self).test_get_validated_token
        )
        await _test_get_validated_token(monkeypatch=monkeypatch)

    @pytest.mark.django_db
    async def test_get_user(self):
        _test_get_user = sync_to_async(super(TestAsyncJWTAuth, self).test_get_user)
        await _test_get_user()


class TestAsyncJWTTokenUserAuth(TestJWTTokenUserAuth):
    def init_backend(self):
        self.backend = authentication.AsyncJWTTokenUserAuth()

    @pytest.mark.django_db
    async def test_get_user(self):
        _test_get_user = sync_to_async(super().test_get_user)
        await _test_get_user()

    @pytest.mark.django_db
    async def test_custom_tokenuser(self, monkeypatch):
        _test_custom_tokenuser = sync_to_async(super().test_custom_tokenuser)
        await _test_custom_tokenuser(monkeypatch=monkeypatch)
