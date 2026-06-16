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
from uuid import UUID

from feeds import repositories as feeds_repositories
from feeds.models import FeedItem, FeedItemReadStatus
from ninja_jwt.utils import aware_utcnow
from users.models import User


async def list_active_feed_items(user: User) -> list[FeedItem]:
    return await feeds_repositories.list_active_feed_items(user=user, at=aware_utcnow())


async def mark_feed_items_as_read(
    user: User, ids: Iterable[UUID]
) -> list[FeedItemReadStatus]:
    return await feeds_repositories.bulk_mark_as_read(user=user, feed_item_ids=ids)
