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

from datetime import timedelta

import pytest

from feeds import repositories
from feeds.models import FeedItemReadStatus, FeedItemType
from ninja_jwt.utils import aware_utcnow
from tests.utils import factories as f

pytestmark = pytest.mark.django_db


##########################################################
# list_active_feed_items
##########################################################


async def test_list_active_returns_only_active_with_read_at():
    now = aware_utcnow()
    user = await f.create_user()
    other = await f.create_user()
    read_item = await f.create_feed_item(
        type=FeedItemType.RELEASE,
        publication_date=now - timedelta(days=1),
        expiration_date=None,
    )
    unread_item = await f.create_feed_item(
        type=FeedItemType.CALL_TO_ACTION,
        publication_date=now - timedelta(days=1),
    )
    scheduled = await f.create_feed_item(
        type=FeedItemType.CALL_TO_ACTION,
        publication_date=now + timedelta(days=1),
    )
    expired = await f.create_feed_item(
        type=FeedItemType.CALL_TO_ACTION,
        publication_date=now - timedelta(days=5),
        expiration_date=now - timedelta(days=1),
    )
    await f.create_feed_item_read_status(feed_item=read_item, user=user)

    items = await repositories.list_active_feed_items(user=user, at=now)

    by_id = {item.id: item for item in items}
    # Only the two active items: the scheduled (future) and expired (past) ones
    # are excluded.
    assert len(items) == 2
    assert read_item.id in by_id
    assert unread_item.id in by_id
    assert scheduled.id not in by_id
    assert expired.id not in by_id
    assert by_id[read_item.id].read_at is not None
    assert by_id[unread_item.id].read_at is None

    items_other = await repositories.list_active_feed_items(user=other, at=now)
    assert all(item.read_at is None for item in items_other)


async def test_list_active_orders_maintenance_first_then_recent():
    now = aware_utcnow()
    user = await f.create_user()
    maintenance = await f.create_feed_item(
        type=FeedItemType.MAINTENANCE,
        publication_date=now - timedelta(days=10),
        expiration_date=now + timedelta(days=1),
    )
    older = await f.create_feed_item(
        type=FeedItemType.CALL_TO_ACTION,
        publication_date=now - timedelta(days=5),
    )
    newer = await f.create_feed_item(
        type=FeedItemType.CALL_TO_ACTION,
        publication_date=now - timedelta(days=1),
    )

    items = await repositories.list_active_feed_items(user=user, at=now)

    assert items[0].id == maintenance.id
    assert [item.id for item in items[1:]] == [newer.id, older.id]


##########################################################
# bulk_mark_as_read
##########################################################


async def test_bulk_mark_as_read_is_idempotent():
    user = await f.create_user()
    item = await f.create_feed_item()

    await repositories.bulk_mark_as_read(user=user, feed_item_ids=[item.id])
    await repositories.bulk_mark_as_read(user=user, feed_item_ids=[item.id])

    count = await FeedItemReadStatus.objects.filter(user=user, feed_item=item).acount()
    assert count == 1
