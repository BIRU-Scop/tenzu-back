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

from events import events_manager
from notifications.events.content import CreateNotificationContent, ReadNotificationsContent
from notifications.models import Notification
from users.models import User

CREATE_NOTIFICATION = "notifications.create"
READ_NOTIFICATIONS = "notifications.read"


async def emit_event_when_notifications_are_created(
    notifications: list[Notification],
) -> None:
    for notification in notifications:
        await events_manager.publish_on_user_channel(
            user=notification.owner,
            type=CREATE_NOTIFICATION,
            content=CreateNotificationContent(
                notification=notification,
            ),
        )


async def emit_event_when_notifications_are_read(user: User, notifications: list[Notification]) -> None:
    await events_manager.publish_on_user_channel(
        user=user,
        type=READ_NOTIFICATIONS,
        content=ReadNotificationsContent(
            notifications_ids=[n.id for n in notifications],
        ),
    )
