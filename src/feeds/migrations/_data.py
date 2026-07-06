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

from django.db.backends.postgresql.psycopg_any import DateTimeTZRange

from feeds.models import FeedItem, FeedItemType


def apply_release(
    FeedItemModel: type[FeedItem], *, title: str, content: str, now: datetime
) -> FeedItem:
    previous = FeedItemModel.objects.filter(
        type=FeedItemType.RELEASE, active_period__upper_inf=True
    ).first()
    if previous is not None:
        previous.active_period = DateTimeTZRange(
            previous.active_period.lower, now, bounds="[)"
        )
        previous.save(update_fields=["active_period"])

    return FeedItemModel.objects.create(
        title=title,
        content=content,
        type=FeedItemType.RELEASE,
        active_period=DateTimeTZRange(now, None, bounds="[)"),
    )
