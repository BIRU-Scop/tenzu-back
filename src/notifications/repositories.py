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
from typing import Any, Literal, TypedDict
from uuid import UUID

from django.db.models import Count, Q

from base.utils.datetime import aware_utcnow
from notifications.models import Notification
from users.models import User

##########################################################
# filters and querysets
##########################################################


class NotificationFilters(TypedDict, total=False):
    id: UUID
    owner: User
    read_at__isnull: bool
    read_at__lt: datetime


NotificationSelectRelated = list[Literal["owner", "created_by"]]


##########################################################
# create notifications
##########################################################


async def create_notifications(
    owner_ids: Iterable[UUID],
    created_by: User,
    notification_type: str,
    content: dict[str, Any],
) -> list[Notification]:
    notifications = [
        Notification(
            owner_id=owner_id,
            created_by=created_by,
            type=notification_type,
            content=content,
        )
        for owner_id in owner_ids
    ]

    return await Notification.objects.abulk_create(notifications)


##########################################################
# list notifications
##########################################################


async def list_notifications(
    filters: NotificationFilters = {},
    offset: int | None = None,
    limit: int | None = None,
    select_related: NotificationSelectRelated = ["created_by"],
) -> list[Notification]:
    qs = Notification.objects.all().filter(**filters).select_related(*select_related)

    if limit is not None and offset is not None:
        limit += offset

    return [a async for a in qs[offset:limit]]


##########################################################
# get notifications
##########################################################


async def get_notification(
    filters: NotificationFilters = {},
    select_related: NotificationSelectRelated = ["created_by"],
) -> Notification | None:
    qs = Notification.objects.all().filter(**filters).select_related(*select_related)

    try:
        return await qs.aget()
    except Notification.DoesNotExist:
        return None


##########################################################
# mark notificatiosn as read
##########################################################


async def mark_notifications_as_read(
    filters: NotificationFilters = {},
    select_related: NotificationSelectRelated = ["created_by"],
) -> list[Notification]:
    qs = Notification.objects.all().filter(**filters).select_related(*select_related)
    await qs.aupdate(read_at=aware_utcnow())
    return [a async for a in qs.all()]


##########################################################
# delete notifications
##########################################################


async def delete_notifications(filters: NotificationFilters = {}) -> int:
    qs = Notification.objects.all().filter(**filters)
    count, _ = await qs.adelete()
    return count


##########################################################
# misc
##########################################################


async def count_notifications(
    filters: NotificationFilters = {},
) -> dict[str, int]:
    return await Notification.objects.filter(**filters).aaggregate(
        read=Count("pk", filter=Q(read_at__isnull=False)),
        unread=Count("pk", filter=Q(read_at__isnull=True)),
    )
