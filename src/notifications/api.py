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

from uuid import UUID

from ninja import Path, Router

from commons.exceptions import api as ex
from commons.exceptions.api.errors import (
    ERROR_RESPONSE_403,
    ERROR_RESPONSE_404,
    ERROR_RESPONSE_422,
)
from commons.validators import B64UUID
from notifications import services as notifications_services
from notifications.models import Notification
from notifications.permissions import NotificationPermissionsCheck
from notifications.serializers import (
    NotificationCountersSerializer,
    NotificationSerializer,
)
from permissions import check_permissions

notifications_router = Router()

##########################################################
# list notifications
##########################################################


@notifications_router.get(
    "/notifications",
    url_name="notifications.list",
    summary="List all the user notifications",
    response={200: list[NotificationSerializer], 403: ERROR_RESPONSE_403},
    by_alias=True,
)
async def list_my_notifications(
    request, read: bool | None = None
) -> list[Notification]:
    """
    List the notifications of the logged user.
    """
    await check_permissions(
        permissions=NotificationPermissionsCheck.ACCESS_SELF.value,
        user=request.user,
        obj=None,
    )
    return await notifications_services.list_user_notifications(
        user=request.user, is_read=read
    )


##########################################################
# count notifications
##########################################################


@notifications_router.get(
    "/notifications/count",
    url_name="notifications.count",
    summary="Counts all the user notifications by type",
    response={200: NotificationCountersSerializer, 403: ERROR_RESPONSE_403},
    by_alias=True,
)
async def count_my_notifications(request) -> dict[str, int]:
    """
    Get user notifications counters
    """
    await check_permissions(
        permissions=NotificationPermissionsCheck.ACCESS_SELF.value,
        user=request.user,
        obj=None,
    )
    return await notifications_services.count_user_notifications(user=request.user)


##########################################################
# mark notification as read
##########################################################


@notifications_router.post(
    "/notifications/read",
    url_name="notifications.mark.all.read",
    summary="Mark all notifications as read",
    response={
        200: list[NotificationSerializer],
        403: ERROR_RESPONSE_403,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def mark_all_my_notification_as_read(
    request,
) -> list[Notification]:
    """
    Mark all user notifications as read.
    """
    await check_permissions(
        permissions=NotificationPermissionsCheck.ACCESS_SELF.value,
        user=request.user,
    )
    return await notifications_services.mark_user_notifications_as_read(
        user=request.user,
    )


@notifications_router.post(
    "/notifications/{notification_id}/read",
    url_name="notifications.mark.read",
    summary="Mark notification as read",
    response={
        200: NotificationSerializer,
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def mark_my_notification_as_read(
    request,
    notification_id: Path[B64UUID],
) -> Notification:
    """
    Mark a notification as read.
    """
    notification = await get_notification_or_404(notification_id=notification_id)
    await check_permissions(
        permissions=NotificationPermissionsCheck.MODIFY.value,
        user=request.user,
        obj=notification,
    )
    return (
        await notifications_services.mark_user_notifications_as_read(
            user=request.user, notification_id=notification_id
        )
    )[0]


##########################################################
# misc
##########################################################


async def get_notification_or_404(notification_id: UUID) -> Notification:
    notification = await notifications_services.get_notification(
        notification_id=notification_id
    )
    if notification is None:
        raise ex.NotFoundError("Notification does not exist")

    return notification
