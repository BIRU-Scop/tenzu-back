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
from django.db import DataError, IntegrityError

from feeds.models import FeedItemType
from ninja_jwt.utils import aware_utcnow
from tests.utils import factories as f

pytestmark = pytest.mark.django_db


##########################################################
# FeedItem.is_active
##########################################################


def test_is_active_published_without_expiration():
    now = aware_utcnow()
    item = f.build_feed_item(
        publication_date=now - timedelta(days=1), expiration_date=None
    )
    assert item.is_active(now) is True


def test_is_active_within_window():
    now = aware_utcnow()
    item = f.build_feed_item(
        publication_date=now - timedelta(days=1),
        expiration_date=now + timedelta(days=1),
    )
    assert item.is_active(now) is True


def test_is_active_not_yet_published():
    now = aware_utcnow()
    item = f.build_feed_item(publication_date=now + timedelta(days=1))
    assert item.is_active(now) is False


def test_is_active_expired():
    now = aware_utcnow()
    item = f.build_feed_item(
        publication_date=now - timedelta(days=2),
        expiration_date=now - timedelta(days=1),
    )
    assert item.is_active(now) is False


##########################################################
# Single active release constraint
##########################################################


def test_only_one_release_without_expiration():
    f.FeedItemFactory.create(type=FeedItemType.RELEASE, expiration_date=None)

    with pytest.raises(IntegrityError):
        f.FeedItemFactory.create(type=FeedItemType.RELEASE, expiration_date=None)


def test_closed_release_allows_a_new_active_one():
    now = aware_utcnow()
    f.FeedItemFactory.create(
        type=FeedItemType.RELEASE,
        publication_date=now - timedelta(days=10),
        expiration_date=now,
    )

    item = f.FeedItemFactory.create(type=FeedItemType.RELEASE, expiration_date=None)

    assert item.id


##########################################################
# Maintenance non-overlapping exclusion constraint
##########################################################


def test_overlapping_maintenance_rejected():
    now = aware_utcnow()
    f.FeedItemFactory.create(
        type=FeedItemType.MAINTENANCE,
        publication_date=now,
        expiration_date=now + timedelta(days=5),
    )

    with pytest.raises(IntegrityError):
        f.FeedItemFactory.create(
            type=FeedItemType.MAINTENANCE,
            publication_date=now + timedelta(days=3),
            expiration_date=now + timedelta(days=8),
        )


def test_contiguous_maintenance_rejected():
    now = aware_utcnow()
    f.FeedItemFactory.create(
        type=FeedItemType.MAINTENANCE,
        publication_date=now,
        expiration_date=now + timedelta(days=5, seconds=1),
    )

    with pytest.raises(IntegrityError):
        f.FeedItemFactory.create(
            type=FeedItemType.MAINTENANCE,
            publication_date=now + timedelta(days=5),
            expiration_date=now + timedelta(days=8),
        )


def test_disjoint_maintenance_allowed():
    now = aware_utcnow()
    f.FeedItemFactory.create(
        type=FeedItemType.MAINTENANCE,
        publication_date=now,
        expiration_date=now + timedelta(days=5),
    )

    item = f.FeedItemFactory.create(
        type=FeedItemType.MAINTENANCE,
        publication_date=now + timedelta(days=5),
        expiration_date=now + timedelta(days=8),
    )

    assert item.id


##########################################################
# Call-to-action check constraint
##########################################################


def test_call_to_action_requires_action_fields():
    with pytest.raises(IntegrityError):
        f.FeedItemFactory.create(
            type=FeedItemType.CALL_TO_ACTION,
            action_title="",
            action_url="",
        )


##########################################################
# Expiration before publication (Postgres rejects lower > upper)
##########################################################


def test_expiration_before_publication_rejected():
    now = aware_utcnow()
    with pytest.raises(DataError):
        f.FeedItemFactory.create(
            type=FeedItemType.RELEASE,
            publication_date=now,
            expiration_date=now - timedelta(days=1),
        )


##########################################################
# FeedItemReadStatus uniqueness
##########################################################


def test_read_status_unique_per_user_and_item():
    status = f.FeedItemReadStatusFactory.create()
    with pytest.raises(IntegrityError):
        f.FeedItemReadStatusFactory.create(feed_item=status.feed_item, user=status.user)
