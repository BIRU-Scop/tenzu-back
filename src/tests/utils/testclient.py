# -*- coding: utf-8 -*-
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
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any
from unittest.mock import Mock

import pytest
from django.test import Client
from ninja.testing import (
    TestAsyncClient as TestAsyncClientBase,
)
from ninja.testing import (
    TestClient as TestClientBase,
)
from ninja.testing.client import NinjaClientBase

from configurations.api import api

if TYPE_CHECKING:
    from users.models import User


class TextClientAuthMixin(NinjaClientBase):
    def login(self, user: "User") -> None:
        from ninja_jwt.tokens import AccessToken

        token = AccessToken.for_user(user)
        self.headers["Authorization"] = f"Bearer {str(token)}"

    def logout(self) -> None:
        self.headers.pop("Authorization", None)

    def _build_request(
        self, method: str, path: str, data: dict, request_params: Any
    ) -> Mock:
        request = super()._build_request(
            method=method, path=path, data=data, request_params=request_params
        )
        request.allauth = SimpleNamespace()
        return request


class TestAsyncClient(TextClientAuthMixin, TestAsyncClientBase):
    pass


class TestSyncClient(TextClientAuthMixin, TestClientBase):
    pass


# TODO have a client for websocket urls
# See https://channels.readthedocs.io/en/latest/topics/testing.html
# test_app.mount("/events/", app=events_app)


@pytest.fixture(scope="function")
def client(monkeypatch):
    monkeypatch.setenv("NINJA_SKIP_REGISTRY", "true")
    return TestAsyncClient(api)


@pytest.fixture(scope="function")
def sync_client(monkeypatch):
    monkeypatch.setenv("NINJA_SKIP_REGISTRY", "true")
    return TestSyncClient(api)


@pytest.fixture(scope="function")
def ssr_client(monkeypatch):
    monkeypatch.setenv("NINJA_SKIP_REGISTRY", "true")
    return Client()
