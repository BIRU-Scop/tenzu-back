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

from unittest.mock import call, patch

from base.serializers import BaseModel
from base.utils.datetime import aware_utcnow
from notifications import services
from tests.utils import factories as f


class SampleContent(BaseModel):
    msg: str


#####################################################################
# notify_users
#####################################################################


async def test_notify_users():
    user = f.build_user()
    notification = f.build_notification(type="test", owner=user)
    content = SampleContent(msg="Test notify")

    with (
        patch(
            "notifications.services.notifications_repositories", autospec=True
        ) as fake_notifications_repository,
        patch(
            "notifications.services.notifications_events", autospec=True
        ) as fake_notifications_events,
    ):
        fake_notifications_repository.create_notifications.return_value = [notification]

        await services.notify_users(
            type="test", emitted_by=user, notified_users=[user], content=content
        )

        fake_notifications_repository.create_notifications.assert_called_once_with(
            owners=[user],
            created_by=user,
            notification_type="test",
            content={"msg": "Test notify"},
        )

        fake_notifications_events.emit_event_when_notifications_are_created.assert_called_once_with(
            notifications=[notification]
        )


#####################################################################
# list_user_notifications
#####################################################################


async def test_list_user_notifications():
    user = f.build_user()

    with patch(
        "notifications.services.notifications_repositories", autospec=True
    ) as fake_notifications_repository:
        await services.list_user_notifications(user=user)

        fake_notifications_repository.list_notifications.assert_called_once_with(
            filters={"owner": user}
        )


async def test_list_user_notifications_read_only():
    user = f.build_user()

    with patch(
        "notifications.services.notifications_repositories", autospec=True
    ) as fake_notifications_repository:
        await services.list_user_notifications(user=user, is_read=True)

        fake_notifications_repository.list_notifications.assert_called_once_with(
            filters={"owner": user, "is_read": True}
        )


async def test_list_user_notifications_unread_only():
    user = f.build_user()

    with patch(
        "notifications.services.notifications_repositories", autospec=True
    ) as fake_notifications_repository:
        await services.list_user_notifications(user=user, is_read=False)

        fake_notifications_repository.list_notifications.assert_called_once_with(
            filters={"owner": user, "is_read": False}
        )


#####################################################################
# mark_user_notifications_as_read
#####################################################################


async def test_mark_user_notifications_as_read_with_one():
    user = f.build_user()
    notification = f.build_notification(owner=user)

    with (
        patch(
            "notifications.services.notifications_repositories", autospec=True
        ) as fake_notifications_repository,
        patch(
            "notifications.services.notifications_events", autospec=True
        ) as fake_notifications_events,
    ):
        fake_notifications_repository.mark_notifications_as_read.return_value = [
            notification
        ]

        notifications = await services.mark_user_notifications_as_read(
            user=user, id=notification.id
        )

        assert notifications == [notification]

        fake_notifications_repository.mark_notifications_as_read.assert_called_once_with(
            filters={"owner": user, "id": notification.id}
        )

        fake_notifications_events.emit_event_when_notifications_are_read.assert_called_once_with(
            user=user, notifications=notifications
        )


async def test_mark_user_notifications_as_read_with_many():
    user = f.build_user()
    notif1 = f.build_notification(owner=user)
    notif2 = f.build_notification(owner=user)
    notif3 = f.build_notification(owner=user)

    with (
        patch(
            "notifications.services.notifications_repositories", autospec=True
        ) as fake_notifications_repository,
        patch(
            "notifications.services.notifications_events", autospec=True
        ) as fake_notifications_events,
    ):
        fake_notifications_repository.mark_notifications_as_read.return_value = [
            notif3,
            notif2,
            notif1,
        ]

        notifications = await services.mark_user_notifications_as_read(user=user)

        assert notifications == [notif3, notif2, notif1]

        fake_notifications_repository.mark_notifications_as_read.assert_called_once_with(
            filters={"owner": user}
        )

        fake_notifications_events.emit_event_when_notifications_are_read.assert_called_once_with(
            user=user, notifications=notifications
        )


#####################################################################
# clean_read_notifications
#####################################################################


async def test_clean_read_notifications():
    now = aware_utcnow()

    with (
        patch(
            "notifications.services.notifications_repositories", autospec=True
        ) as fake_notifications_repository,
    ):
        fake_notifications_repository.delete_notifications.return_value = 1

        assert await services.clean_read_notifications(before=now) == 1

        fake_notifications_repository.delete_notifications.assert_called_once_with(
            filters={
                "is_read": True,
                "read_before": now,
            }
        )


#####################################################################
# count_user_notifications
#####################################################################


async def test_count_user_notifications():
    user = f.build_user()

    with patch(
        "notifications.services.notifications_repositories", autospec=True
    ) as fake_notifications_repository:
        fake_notifications_repository.count_notifications.side_effect = [10, 2]

        result = await services.count_user_notifications(user=user)

        assert result == {"total": 10, "read": 2, "unread": 8}

        fake_notifications_repository.count_notifications.assert_has_awaits(
            [
                call(filters={"owner": user}),
                call(filters={"owner": user, "is_read": True}),
            ]
        )
