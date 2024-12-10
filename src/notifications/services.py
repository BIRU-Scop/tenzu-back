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

from collections.abc import Iterable
from datetime import datetime
from uuid import UUID

from base.serializers import BaseModel
from notifications import events as notifications_events
from notifications import repositories as notifications_repositories
from notifications.models import Notification
from notifications.repositories import NotificationFilters
from users.models import User


async def notify_users(
    type: str, emitted_by: User, notified_users: Iterable[User], content: BaseModel
) -> None:
    notifications = await notifications_repositories.create_notifications(
        owners=notified_users,
        created_by=emitted_by,
        notification_type=type,
        content=content.dict(),
    )
    await notifications_events.emit_event_when_notifications_are_created(
        notifications=notifications
    )


async def list_user_notifications(
    user: User, is_read: bool | None = None
) -> list[Notification]:
    filters: NotificationFilters = {"owner": user}

    if is_read is not None:
        filters["is_read"] = is_read

    return await notifications_repositories.list_notifications(filters=filters)


async def get_user_notification(user: User, id: UUID) -> Notification | None:
    return await notifications_repositories.get_notification(
        filters={"owner": user, "id": id}
    )


async def mark_user_notifications_as_read(
    user: User, id: UUID | None = None
) -> list[Notification]:
    filters: NotificationFilters = {"owner": user}

    if id is not None:
        filters["id"] = id

    notifications = await notifications_repositories.mark_notifications_as_read(
        filters=filters
    )

    if notifications:
        await notifications_events.emit_event_when_notifications_are_read(
            user=user, notifications=notifications
        )

    return notifications


async def count_user_notifications(user: User) -> dict[str, int]:
    total = await notifications_repositories.count_notifications(
        filters={"owner": user}
    )
    read = await notifications_repositories.count_notifications(
        filters={"owner": user, "is_read": True}
    )
    return {"total": total, "read": read, "unread": total - read}


async def clean_read_notifications(before: datetime) -> int:
    return await notifications_repositories.delete_notifications(
        filters={"is_read": True, "read_before": before}
    )
