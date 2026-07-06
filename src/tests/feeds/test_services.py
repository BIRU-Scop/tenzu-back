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

import uuid
from unittest.mock import ANY, patch

from feeds import services
from tests.utils import factories as f

#####################################################################
# list_active_feed_items
#####################################################################


async def test_list_active_feed_items_delegates_to_repository():
    user = f.build_user()
    expected = [f.build_feed_item(), f.build_feed_item()]

    with patch("feeds.services.feeds_repositories", autospec=True) as fake_repo:
        fake_repo.list_active_feed_items.return_value = expected

        result = await services.list_active_feed_items(user=user)

        assert result == expected
        fake_repo.list_active_feed_items.assert_called_once_with(user=user, at=ANY)


#####################################################################
# mark_feed_items_as_read
#####################################################################


async def test_mark_feed_items_as_read_marks_and_returns_them():
    user = f.build_user()
    ids = [uuid.uuid7(), uuid.uuid7()]

    created = [object(), object()]

    with patch("feeds.services.feeds_repositories", autospec=True) as fake_repo:
        fake_repo.bulk_mark_as_read.return_value = created

        result = await services.mark_feed_items_as_read(user=user, ids=ids)

        assert result == created
        fake_repo.bulk_mark_as_read.assert_called_once_with(
            user=user, feed_item_ids=ids
        )
