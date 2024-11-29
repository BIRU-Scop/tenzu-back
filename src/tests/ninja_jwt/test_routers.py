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

import pytest

from ninja_jwt.tokens import RefreshToken, SlidingToken
from tests.utils.factories import create_user
from users.models import User


@pytest.mark.django_db
class TestObtainTokenRouter:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.username = "test_user"
        self.password = "test_password"
        self.user = create_user(
            email="test@user.com",
            username="test_user",
            password="test_password",
            is_active=True,
        )
        self.user.set_password(self.password)
        self.user.save()

    def test_obtain_token_pair_success(self, client):
        response = client.post(
            "/token",
            json={
                User.USERNAME_FIELD: self.username,
                "password": self.password,
            },
            content_type="application/json",
        )
        assert response.status_code == 200

        assert "access" in response.json()
        assert "refresh" in response.json()
        assert User.USERNAME_FIELD in response.json()

    def test_obtain_token_pair_fail(self, client):
        response = client.post(
            "/token",
            json={
                User.USERNAME_FIELD: self.username,
                "password": "wrong_password",
            },
            content_type="application/json",
        )
        assert response.status_code == 401

        assert "detail" in response.json()
        assert "code" in response.json()

    def test_obtain_token_pair_fail_user_not_active(self, client):
        self.user.is_active = False
        self.user.save()

        response = client.post(
            "/token",
            json={
                User.USERNAME_FIELD: self.username,
                "password": self.password,
            },
            content_type="application/json",
        )
        assert response.status_code == 401

        assert "detail" in response.json()
        assert "code" in response.json()

    def test_refresh_token_success(self, client):
        token = RefreshToken.for_user(self.user)

        response = client.post(
            "/token/refresh",
            json={
                "refresh": str(token),
            },
            content_type="application/json",
        )
        assert response.status_code == 200

        assert "access" in response.json()
        assert "refresh" in response.json()

    def test_refresh_token_fail(self, client):
        response = client.post(
            "/token/refresh",
            json={
                "refresh": "wrong_refresh_token",
            },
            content_type="application/json",
        )
        assert response.status_code == 401

        assert "detail" in response.json()
        assert "code" in response.json()

    def test_obtain_token_sliding_success(self, client):
        response = client.post(
            "/sliding",
            json={
                User.USERNAME_FIELD: self.username,
                "password": self.password,
            },
            content_type="application/json",
        )
        assert response.status_code == 200

        assert "token" in response.json()
        assert User.USERNAME_FIELD in response.json()

    def test_obtain_token_sliding_fail(self, client):
        response = client.post(
            "/sliding",
            json={
                User.USERNAME_FIELD: self.username,
                "password": "wrong_password",
            },
            content_type="application/json",
        )
        assert response.status_code == 401

        assert "detail" in response.json()
        assert "code" in response.json()

    def test_obtain_token_sliding_fail_user_not_active(self, client):
        self.user.is_active = False
        self.user.save()

        response = client.post(
            "/sliding",
            json={
                User.USERNAME_FIELD: self.username,
                "password": self.password,
            },
            content_type="application/json",
        )
        assert response.status_code == 401

        assert "detail" in response.json()
        assert "code" in response.json()

    def test_refresh_sliding_token_success(self, client):
        token = SlidingToken.for_user(self.user)

        response = client.post(
            "/sliding/refresh",
            json={"token": str(token)},
            content_type="application/json",
        )
        assert response.status_code == 200

        assert "token" in response.json()

    def test_refresh_sliding_token_token_fail(self, client):
        token = SlidingToken.for_user(self.user)
        response = client.post(
            "/token/refresh",
            json={"refresh": str(token)},
            content_type="application/json",
        )
        assert response.status_code == 401

        assert "detail" in response.json()
        assert "code" in response.json()

    def test_verify_token_success(self, client):
        token = RefreshToken.for_user(self.user)
        response = client.post(
            "/verify",
            json={
                "token": str(token),
            },
            content_type="application/json",
        )
        assert response.status_code == 200

    def test_verify_token_fail(self, client):
        response = client.post(
            "/verify",
            json={
                "token": "wrong_token",
            },
            content_type="application/json",
        )
        assert response.status_code == 401

        assert "detail" in response.json()
        assert "code" in response.json()

    def test_blacklist_token_success(self, client):
        token = RefreshToken.for_user(self.user)
        response = client.post(
            "/blacklist",
            json={
                "refresh": str(token),
            },
            content_type="application/json",
        )
        assert response.status_code == 200
