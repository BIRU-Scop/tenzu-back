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

from datetime import datetime
from uuid import UUID

from base.serializers import UUIDB64, BaseSchema


class FeedItemSerializer(BaseSchema):
    id: UUIDB64
    title: str
    content: str
    type: str
    action_title: str
    action_url: str
    publication_date: datetime
    expiration_date: datetime | None = None
    # Annotated by the repository: read date for the current user (null if the
    # item has not been read).
    read_at: datetime | None = None


class FeedItemUpdateReadSerializer(BaseSchema):
    """
    Built from `FeedItemReadStatus` rows.
    """

    id: UUIDB64
    read_at: datetime

    @staticmethod
    def resolve_id(obj) -> UUID:
        return obj.feed_item_id
