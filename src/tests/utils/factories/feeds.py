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

from asgiref.sync import sync_to_async
from django.db.backends.postgresql.psycopg_any import DateTimeTZRange

from feeds.models import FeedItemType
from ninja_jwt.utils import aware_utcnow

from .base import Factory, factory


class FeedItemFactory(Factory):
    title = factory.Sequence(lambda n: f"Feed item {n}")
    content = factory.Sequence(lambda n: f"# Update {n}\n\nSome **markdown** content.")
    type = FeedItemType.CALL_TO_ACTION
    action_title = "Act now"
    action_url = "https://example.com"
    active_period = factory.LazyAttribute(
        lambda o: DateTimeTZRange(o.publication_date, o.expiration_date, bounds="[)")
    )

    class Params:
        publication_date = factory.LazyFunction(aware_utcnow)
        expiration_date = None

    class Meta:
        model = "feeds.FeedItem"


class FeedItemReadStatusFactory(Factory):
    feed_item = factory.SubFactory(FeedItemFactory)
    user = factory.SubFactory("tests.utils.factories.UserFactory")

    class Meta:
        model = "feeds.FeedItemReadStatus"


@sync_to_async
def create_feed_item(**kwargs):
    return FeedItemFactory.create(**kwargs)


def build_feed_item(**kwargs):
    return FeedItemFactory.build(**kwargs)


@sync_to_async
def create_feed_item_read_status(**kwargs):
    return FeedItemReadStatusFactory.create(**kwargs)
