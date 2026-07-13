# Copyright (C) 2026 BIRU
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

from django.db.models import (
    Case,
    IntegerField,
    OuterRef,
    Q,
    Subquery,
    Value,
    When,
)

from feeds.models import FeedItem, FeedItemReadStatus, FeedItemType
from users.models import User


def _active_filter(at: datetime) -> Q:
    return Q(active_period__contains=at)


def _read_at_subquery(user: User) -> Subquery:
    return Subquery(
        FeedItemReadStatus.objects.filter(feed_item=OuterRef("pk"), user=user).values(
            "read_at"
        )[:1]
    )


##########################################################
# list feed items
##########################################################


async def list_active_feed_items(user: User, at: datetime) -> list[FeedItem]:
    qs = (
        FeedItem.objects.filter(_active_filter(at))
        .annotate(read_at=_read_at_subquery(user))
        # Active maintenance (at most one) first, then most recent. Ordering on
        # the lower bound of the period (= publication date).
        .order_by(
            Case(
                When(type=FeedItemType.MAINTENANCE, then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            ),
            "-active_period__startswith",
        )
    )
    return [item async for item in qs]


##########################################################
# mark as read
##########################################################


async def bulk_mark_as_read(
    user: User, feed_item_ids: Iterable[UUID]
) -> list[FeedItemReadStatus]:
    statuses = [
        FeedItemReadStatus(user=user, feed_item_id=feed_item_id)
        for feed_item_id in feed_item_ids
    ]
    return await FeedItemReadStatus.objects.abulk_create(
        statuses, ignore_conflicts=True
    )
