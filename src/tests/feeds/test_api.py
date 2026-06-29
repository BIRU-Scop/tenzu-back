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

from feeds.models import FeedItemReadStatus, FeedItemType
from ninja_jwt.utils import aware_utcnow
from tests.utils import factories as f
from tests.utils.bad_params import NOT_EXISTING_B64ID

pytestmark = pytest.mark.django_db


##########################################################
# GET /feeds
##########################################################


async def test_list_feeds_200_with_read_flags(client):
    now = aware_utcnow()
    user = await f.create_user()
    read_item = await f.create_feed_item(
        type=FeedItemType.RELEASE,
        publication_date=now - timedelta(days=1),
    )
    unread_item = await f.create_feed_item(
        type=FeedItemType.CALL_TO_ACTION,
        publication_date=now - timedelta(days=1),
    )
    await f.create_feed_item(
        type=FeedItemType.CALL_TO_ACTION,
        publication_date=now + timedelta(days=1),
    )
    await f.create_feed_item_read_status(feed_item=read_item, user=user)

    client.login(user)
    response = await client.get("/feeds")

    assert response.status_code == 200, response.data
    res = response.data["data"]
    assert len(res) == 2
    read_at_by_id = {item["id"]: item["readAt"] for item in res}
    assert read_at_by_id[read_item.b64id] is not None
    assert read_at_by_id[unread_item.b64id] is None


async def test_list_feeds_empty_returns_200_empty_list(client):
    user = await f.create_user()

    client.login(user)
    response = await client.get("/feeds")

    assert response.status_code == 200
    assert response.data["data"] == []


async def test_list_feeds_401_anonymous(client):
    response = await client.get("/feeds")
    assert response.status_code == 401


##########################################################
# POST /feeds/read
##########################################################


async def test_mark_feeds_read_returns_minimal_read_state(client):
    now = aware_utcnow()
    user = await f.create_user()
    item = await f.create_feed_item(
        type=FeedItemType.CALL_TO_ACTION,
        publication_date=now - timedelta(days=1),
    )

    client.login(user)
    response = await client.post("/feeds/read", json={"ids": [item.b64id]})

    assert response.status_code == 200, response.data["data"]
    res = response.data["data"]
    assert len(res) == 1
    assert set(res[0].keys()) == {"id", "readAt"}
    assert res[0]["id"] == item.b64id
    assert res[0]["readAt"] is not None

    stored_read_at = (
        await FeedItemReadStatus.objects.aget(user=user, feed_item=item)
    ).read_at

    response = await client.post("/feeds/read", json={"ids": [item.b64id]})
    assert response.status_code == 200, response.data["data"]
    statuses = [
        s async for s in FeedItemReadStatus.objects.filter(user=user, feed_item=item)
    ]
    assert len(statuses) == 1
    assert statuses[0].read_at == stored_read_at


@pytest.mark.django_db(transaction=True, serialized_rollback=True)
async def test_mark_feeds_read_not_found_id(client):
    user = await f.create_user()

    client.login(user)
    response = await client.post("/feeds/read", json={"ids": [NOT_EXISTING_B64ID]})
    assert response.status_code == 404, response.data


async def test_mark_feeds_read_401_anonymous(client):
    response = await client.post("/feeds/read", json={"ids": [NOT_EXISTING_B64ID]})
    assert response.status_code == 401
