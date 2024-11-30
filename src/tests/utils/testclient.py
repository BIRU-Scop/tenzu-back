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

# TODO (spade): redo when getting rid of main.api

from typing import TYPE_CHECKING

from ninja.testing import TestClient as TestClientBase

if TYPE_CHECKING:
    from users.models import User


class TestClient(TestClientBase):
    def login(self, user: "User") -> None:
        from ninja_jwt.tokens import AccessToken

        token = AccessToken.for_user(user)
        self.headers["Authorization"] = f"Bearer {str(token)}"

    def logout(self) -> None:
        self.headers.pop("Authorization", None)


# TODO have a client for websocket urls
# See https://channels.readthedocs.io/en/latest/topics/testing.html
# test_app.mount("/events/", app=events_app)


def get_client(monkeypatch, router) -> TestClient:
    monkeypatch.setenv("NINJA_SKIP_REGISTRY", "true")
    return TestClient(router)


# @pytest.fixture
# def non_mocked_hosts() -> list[str]:
#     # This is to prevent pytest_httpx from catching calls to the TestClient
#     # https://github.com/Colin-b/pytest_httpx/tree/master#do-not-mock-some-requests
#     return ["testserver"]
