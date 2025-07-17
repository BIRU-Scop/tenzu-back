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

from datetime import timedelta

import pytest

from ninja_jwt.utils import aware_utcnow
from notifications import repositories
from notifications.models import Notification
from tests.utils import factories as f

pytestmark = pytest.mark.django_db


##########################################################
# create notifications
##########################################################


async def test_create_notification():
    user1 = await f.create_user()
    user2 = await f.create_user()
    user3 = await f.create_user()

    notifications = await repositories.create_notifications(
        owner_ids=[user1.id, user2.id],
        created_by=user3,
        notification_type="test_notification",
        content={"msg": "test"},
    )

    assert len(notifications) == 2
    assert notifications[0].created_by == notifications[1].created_by == user3
    assert notifications[0].type == notifications[1].type == "test_notification"
    assert notifications[0].content == notifications[1].content == {"msg": "test"}
    assert notifications[0].owner_id == user1.id
    assert notifications[1].owner_id == user2.id


##########################################################
# list notifications
##########################################################


async def test_list_notifications_filters():
    user1 = await f.create_user()
    user2 = await f.create_user()
    user3 = await f.create_user()

    now = aware_utcnow()

    n11 = await f.create_notification(owner=user1, created_by=user3)
    n12 = await f.create_notification(
        owner=user1, created_by=user3, read_at=now - timedelta(minutes=2)
    )
    n13 = await f.create_notification(owner=user1, created_by=user3)

    n21 = await f.create_notification(owner=user2, created_by=user3)
    n22 = await f.create_notification(
        owner=user2, created_by=user3, read_at=now - timedelta(minutes=1)
    )

    assert [n22, n21, n13, n12, n11] == await repositories.list_notifications()
    assert [n13, n12, n11] == await repositories.list_notifications(
        filters={"owner": user1}
    )
    assert [n13, n11] == await repositories.list_notifications(
        filters={"owner": user1, "read_at__isnull": True}
    )
    assert [n12] == await repositories.list_notifications(
        filters={"owner": user1, "read_at__isnull": False}
    )
    assert [n22, n12] == await repositories.list_notifications(
        filters={"read_at__isnull": False}
    )
    assert [n12] == await repositories.list_notifications(
        filters={"read_at__lt": now - timedelta(minutes=1)}
    )


##########################################################
# get_notification
##########################################################


async def test_get_notification():
    user1 = await f.create_user()
    user2 = await f.create_user()
    notification = await f.create_notification(owner=user1)

    assert (
        await repositories.get_notification(filters={"id": notification.id})
        == notification
    )
    assert (
        await repositories.get_notification(
            filters={"id": notification.id, "owner": user1}
        )
        == notification
    )
    assert (
        await repositories.get_notification(
            filters={"id": notification.id, "owner": user2}
        )
        is None
    )


##########################################################
# mark notifications as read
##########################################################


async def test_mark_notifications_as_read():
    user = await f.create_user()
    n1 = await f.create_notification(owner=user)
    n2 = await f.create_notification(owner=user)
    n3 = await f.create_notification(owner=user)

    assert n1.read_at == n2.read_at == n3.read_at is None

    ns = await repositories.mark_notifications_as_read(filters={"owner": user})

    assert ns[0].read_at == ns[1].read_at == ns[2].read_at is not None


##########################################################
# delete notifications
##########################################################


async def test_delete_notifications():
    user1 = await f.create_user()
    user2 = await f.create_user()
    user3 = await f.create_user()

    now = aware_utcnow()

    await f.create_notification(owner=user1, created_by=user3)
    await f.create_notification(
        owner=user1, created_by=user3, read_at=now - timedelta(minutes=1)
    )
    await f.create_notification(
        owner=user1, created_by=user3, read_at=now - timedelta(minutes=2)
    )

    await f.create_notification(owner=user2, created_by=user3)
    await f.create_notification(
        owner=user2, created_by=user3, read_at=now - timedelta(minutes=1)
    )

    await repositories.delete_notifications(
        filters={"read_at__lt": now - timedelta(minutes=1)}
    )

    assert 4 == await Notification.objects.acount()
    count = await repositories.count_notifications(filters={"owner": user1})
    assert count["read"] == 1
    assert count["unread"] == 1
    count = await repositories.count_notifications(filters={"owner": user2})
    assert count["read"] == 1
    assert count["unread"] == 1

    await repositories.delete_notifications(filters={"read_at__lt": now})

    assert 2 == await Notification.objects.acount()
    count = await repositories.count_notifications(filters={"owner": user1})
    assert count["read"] == 0
    assert count["unread"] == 1
    count = await repositories.count_notifications(filters={"owner": user2})
    assert count["read"] == 0
    assert count["unread"] == 1


##########################################################
# misc
##########################################################


async def test_count_notifications():
    user1 = await f.create_user()
    user2 = await f.create_user()
    user3 = await f.create_user()

    await f.create_notification(owner=user1, created_by=user3)
    await f.create_notification(owner=user1, created_by=user3, read_at=aware_utcnow())
    await f.create_notification(owner=user1, created_by=user3)

    await f.create_notification(owner=user2, created_by=user3)
    await f.create_notification(owner=user2, created_by=user3, read_at=aware_utcnow())

    count = await repositories.count_notifications()
    assert count["read"] == 2
    assert count["unread"] == 3
    count = await repositories.count_notifications(filters={"owner": user1})
    assert count["read"] == 1
    assert count["unread"] == 2
