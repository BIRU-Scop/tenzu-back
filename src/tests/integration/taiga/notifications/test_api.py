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

import pytest
from fastapi import status

from base.utils.datetime import aware_utcnow
from tests.utils import factories as f
from tests.utils.bad_params import INVALID_B64ID

pytestmark = pytest.mark.django_db

##########################################################
# GET my/notifications
##########################################################


async def test_list_my_notifications_200_ok(client):
    user = await f.create_user()
    await f.create_notification(owner=user)
    await f.create_notification(owner=user)
    await f.create_notification(owner=user, read_at=aware_utcnow())

    client.login(user)
    response = client.get("/my/notifications")
    assert response.status_code == status.HTTP_200_OK, response.text
    assert len(response.json()) == 3


async def test_list_my_notifications_200_ok_filter_only_read(client):
    user = await f.create_user()
    await f.create_notification(owner=user)
    await f.create_notification(owner=user)
    await f.create_notification(owner=user, read_at=aware_utcnow())

    client.login(user)
    response = client.get("/my/notifications", params={"read": True})
    assert response.status_code == status.HTTP_200_OK, response.text
    assert len(response.json()) == 1


async def test_list_my_notifications_200_ok_filter_only_unread(client):
    user = await f.create_user()
    await f.create_notification(owner=user)
    await f.create_notification(owner=user)
    await f.create_notification(owner=user, read_at=aware_utcnow())

    client.login(user)
    response = client.get("/my/notifications", params={"read": False})
    assert response.status_code == status.HTTP_200_OK, response.text
    assert len(response.json()) == 2


async def test_list_my_notifications_403_forbidden_error(client):
    user = await f.create_user()
    await f.create_notification(owner=user)

    response = client.get("/my/notifications")
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.text


##########################################################
# POST my/notifications/{id}/read
##########################################################


async def test_mark_notification_as_read_200_ok(client):
    user = await f.create_user()
    notification = await f.create_notification(owner=user)

    client.login(user)
    response = client.post(f"/my/notifications/{notification.b64id}/read")
    assert response.status_code == status.HTTP_200_OK, response.text
    assert response.json()["readAt"] is not None, response.json()


async def test_mark_my_notification_as_read_404_not_found(client):
    user = await f.create_user()
    notification = await f.create_notification()

    client.login(user)
    response = client.post(f"/my/notifications/{notification.b64id}/read")
    assert response.status_code == status.HTTP_404_NOT_FOUND, response.text


async def test_mark_my_notification_as_read_403_forbidden_error(client):
    user = await f.create_user()
    notification = await f.create_notification(owner=user)

    response = client.post(f"/my/notifications/{notification.b64id}/read")
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.text


async def test_mark_my_notification_as_read_422_unprocessable_entity(client):
    user = await f.create_user()

    client.login(user)
    response = client.post(f"/my/notifications/{INVALID_B64ID}/read")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, response.text


##########################################################
# GET my/notifications/count
##########################################################


async def test_count_my_notifications_200_ok(client):
    user = await f.create_user()
    await f.create_notification(owner=user)
    await f.create_notification(owner=user)
    await f.create_notification(owner=user, read_at=aware_utcnow())

    client.login(user)
    response = client.get("/my/notifications/count")
    assert response.status_code == status.HTTP_200_OK, response.text
    assert response.json() == {"total": 3, "read": 1, "unread": 2}


async def test_count_my_notifications_403_forbidden_error(client):
    user = await f.create_user()
    await f.create_notification(owner=user)

    response = client.get("/my/notifications/count")
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.text
