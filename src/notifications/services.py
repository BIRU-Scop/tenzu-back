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
    type: str, emitted_by: User, notified_user_ids: Iterable[UUID], content: BaseModel
) -> None:
    notifications = await notifications_repositories.create_notifications(
        owner_ids=notified_user_ids,
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
        filters["read_at__isnull"] = not is_read

    return await notifications_repositories.list_notifications(filters=filters)


async def get_notification(notification_id: UUID) -> Notification | None:
    return await notifications_repositories.get_notification(
        filters={"id": notification_id}, select_related=["owner", "created_by"]
    )


async def mark_user_notifications_as_read(
    user: User, notification_id: UUID | None = None
) -> list[Notification]:
    filters: NotificationFilters = {"owner": user}

    if notification_id is not None:
        filters["id"] = notification_id

    notifications = await notifications_repositories.mark_notifications_as_read(
        filters=filters
    )

    if notifications:
        await notifications_events.emit_event_when_notifications_are_read(
            user=user, notifications=notifications
        )

    return notifications


async def count_user_notifications(user: User) -> dict[str, int]:
    count = await notifications_repositories.count_notifications(
        filters={"owner": user}
    )
    return {**count, "total": count["read"] + count["unread"]}


async def clean_read_notifications(before: datetime) -> int:
    return await notifications_repositories.delete_notifications(
        filters={"read_at__isnull": False, "read_at__lt": before}
    )
