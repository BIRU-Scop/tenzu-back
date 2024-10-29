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
from typing import Any, TypedDict
from uuid import UUID

from base.db.models import QuerySet
from base.utils.datetime import aware_utcnow
from notifications.models import Notification
from users.models import User

##########################################################
# filters and querysets
##########################################################

DEFAULT_QUERYSET = Notification.objects.select_related("created_by").all()


class NotificationFilters(TypedDict, total=False):
    id: UUID
    owner: User
    is_read: bool
    read_before: datetime


async def _apply_filters_to_queryset(
    qs: QuerySet[Notification],
    filters: NotificationFilters = {},
) -> QuerySet[Notification]:
    filter_data = dict(filters.copy())

    if "is_read" in filter_data:
        is_read = filter_data.pop("is_read")
        filter_data["read_at__isnull"] = not is_read
    if "read_before" in filter_data:
        read_before = filter_data.pop("read_before")
        filter_data["read_at__lt"] = read_before

    return qs.filter(**filter_data)


##########################################################
# create notifications
##########################################################


async def create_notifications(
    owners: Iterable[User],
    created_by: User,
    notification_type: str,
    content: dict[str, Any],
) -> list[Notification]:
    notifications = [
        Notification(
            owner=owner,
            created_by=created_by,
            type=notification_type,
            content=content,
        )
        for owner in owners
    ]

    return await Notification.objects.abulk_create(notifications)


##########################################################
# list notifications
##########################################################


async def list_notifications(
    filters: NotificationFilters = {},
    offset: int | None = None,
    limit: int | None = None,
) -> list[Notification]:
    qs = await _apply_filters_to_queryset(qs=DEFAULT_QUERYSET, filters=filters)

    if limit is not None and offset is not None:
        limit += offset

    return [a async for a in qs[offset:limit]]


##########################################################
# get notifications
##########################################################


async def get_notification(
    filters: NotificationFilters = {},
) -> Notification | None:
    qs = await _apply_filters_to_queryset(qs=DEFAULT_QUERYSET, filters=filters)

    try:
        return await qs.aget()
    except Notification.DoesNotExist:
        return None


##########################################################
# mark notificatiosn as read
##########################################################


async def mark_notifications_as_read(
    filters: NotificationFilters = {},
) -> list[Notification]:
    qs = await _apply_filters_to_queryset(qs=DEFAULT_QUERYSET, filters=filters)
    await qs.aupdate(read_at=aware_utcnow())
    return [a async for a in qs.all()]


##########################################################
# delete notifications
##########################################################


async def delete_notifications(filters: NotificationFilters = {}) -> int:
    qs = await _apply_filters_to_queryset(qs=DEFAULT_QUERYSET, filters=filters)
    count, _ = await qs.adelete()
    return count


##########################################################
# misc
##########################################################


async def count_notifications(
    filters: NotificationFilters = {},
) -> int:
    qs = await _apply_filters_to_queryset(qs=DEFAULT_QUERYSET, filters=filters)

    return await qs.acount()
