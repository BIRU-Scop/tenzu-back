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

import pytest

from ninja_jwt.utils import aware_utcnow
from tests.utils import factories as f
from tests.utils.bad_params import INVALID_B64ID, NOT_EXISTING_B64ID

pytestmark = pytest.mark.django_db

##########################################################
# GET my/notifications
##########################################################


async def test_list_notifications_200_ok(client):
    user = await f.create_user()
    await f.create_notification(owner=user)
    await f.create_notification(owner=user)
    await f.create_notification(owner=user, read_at=aware_utcnow())

    client.login(user)
    response = await client.get("/notifications")
    assert response.status_code == 200, response.data["data"]
    res = response.data["data"]
    assert len(res) == 3


async def test_list_notifications_200_ok_filter_only_read(client):
    user = await f.create_user()
    await f.create_notification(owner=user)
    await f.create_notification(owner=user)
    await f.create_notification(owner=user, read_at=aware_utcnow())

    client.login(user)
    response = await client.get("/notifications?read=true")
    assert response.status_code == 200, response.data["data"]
    res = response.data["data"]
    assert len(res) == 1


async def test_list_notifications_200_ok_filter_only_unread(client):
    user = await f.create_user()
    await f.create_notification(owner=user)
    await f.create_notification(owner=user)
    await f.create_notification(owner=user, read_at=aware_utcnow())

    client.login(user)
    response = await client.get("/notifications?read=false")
    assert response.status_code == 200, response.data["data"]
    res = response.data["data"]
    assert len(res) == 2


async def test_list_notifications_401_forbidden_error_anonymous(client):
    response = await client.get("/notifications")
    assert response.status_code == 401, response.data


##########################################################
# GET my/notifications/count
##########################################################


async def test_count_notifications_200_ok(client):
    user = await f.create_user()
    await f.create_notification(owner=user)
    await f.create_notification(owner=user)
    await f.create_notification(owner=user, read_at=aware_utcnow())

    client.login(user)
    response = await client.get("/notifications/count")
    assert response.status_code == 200, response.data
    res = response.data
    assert res["read"] == 1
    assert res["unread"] == 2
    assert res["total"] == 3


async def test_count_notifications_401_forbidden_error_anonymous(client):
    response = await client.get("/notifications/count")
    assert response.status_code == 401, response.data


##########################################################
# POST my/notifications/read
##########################################################


async def test_mark_all_notifications_as_read_200_ok(client):
    user = await f.create_user()
    await f.create_notification(owner=user)
    await f.create_notification(owner=user)

    client.login(user)
    response = await client.post("/notifications/read")
    assert response.status_code == 200, response.data["data"]
    res = response.data["data"]
    assert len(res) == 2


async def test_mark_all_notifications_as_read_401_anonymous(client):
    response = await client.post("/notifications/read")
    assert response.status_code == 401, response.data


##########################################################
# POST my/notifications/<id>/read
##########################################################


async def test_mark_notification_as_read_200_ok(client):
    user = await f.create_user()
    notification = await f.create_notification(owner=user)

    client.login(user)
    response = await client.post(f"/notifications/{notification.b64id}/read")
    assert response.status_code == 200, response.data["data"]
    res = response.data["data"]
    assert res["readAt"] is not None


async def test_mark_notification_as_read_404_not_found(client):
    user = await f.create_user()

    client.login(user)
    response = await client.post(f"/notifications/{NOT_EXISTING_B64ID}/read")
    assert response.status_code == 404, response.data


async def test_mark_notification_as_read_403_forbidden_error(client):
    user = await f.create_user()
    other_user = await f.create_user()
    notification = await f.create_notification(owner=user)

    client.login(other_user)
    response = await client.post(f"/notifications/{notification.b64id}/read")
    assert response.status_code == 403, response.data


async def test_mark_notification_as_read_401_forbidden_error(client):
    user = await f.create_user()
    notification = await f.create_notification(owner=user)

    response = await client.post(f"/notifications/{notification.b64id}/read")
    assert response.status_code == 401, response.data


async def test_mark_notification_as_read_422_unprocessable_entity(client):
    user = await f.create_user()

    client.login(user)
    response = await client.post(f"/notifications/{INVALID_B64ID}/read")
    assert response.status_code == 422, response.data
