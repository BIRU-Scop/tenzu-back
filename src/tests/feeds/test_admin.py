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
from django.contrib.admin import site
from django.urls import reverse
from martor.widgets import AdminMartorWidget

from feeds.admin import FeedItemAdmin, FeedItemAdminForm
from feeds.models import FeedItem, FeedItemStatus, FeedItemType
from ninja_jwt.utils import aware_utcnow
from tests.utils import factories as f
from tests.utils.admin import admin_field_split_dt

pytestmark = pytest.mark.django_db


##########################################################
# created_by set automatically
##########################################################


def test_get_queryset_annotates_status_and_orders_it(rf, empty_feed_items):
    now = aware_utcnow()
    f.FeedItemFactory.create(
        type=FeedItemType.CALL_TO_ACTION,
        publication_date=now + timedelta(days=1),
    )  # scheduled
    f.FeedItemFactory.create(
        type=FeedItemType.CALL_TO_ACTION,
        publication_date=now - timedelta(days=1),
    )  # active
    f.FeedItemFactory.create(
        type=FeedItemType.CALL_TO_ACTION,
        publication_date=now - timedelta(days=5),
        expiration_date=now - timedelta(days=1),
    )  # expired

    request = rf.get("/admin/feeds/feeditem/")
    request.user = f.UserFactory.create(is_superuser=True)
    model_admin = FeedItemAdmin(FeedItem, site)
    qs = model_admin.get_queryset(request).order_by("status_order")

    items = list(qs)
    assert [item.status for item in items] == [
        FeedItemStatus.SCHEDULED,
        FeedItemStatus.ACTIVE,
        FeedItemStatus.EXPIRED,
    ]

    assert model_admin.status(items[1]) == FeedItemStatus.ACTIVE.label


def test_save_model_sets_created_by_to_session_user(rf, empty_feed_items):
    user = f.UserFactory.create(is_superuser=True)
    request = rf.post("/admin/feeds/feeditem/add/")
    request.user = user
    model_admin = FeedItemAdmin(FeedItem, site)
    item = FeedItem(
        title="A release",
        content="# Notes",
        type=FeedItemType.RELEASE,
    )

    model_admin.save_model(request, item, form=None, change=False)

    assert item.pk is not None
    assert item.created_by == user


##########################################################
# Admin form validation
##########################################################


def _base_form_data(
    *,
    type=FeedItemType.RELEASE,
    publication_date=None,
    expiration_date=None,
    action_title="",
    action_url="",
):
    publication_date = publication_date or aware_utcnow().replace(
        microsecond=0, second=0
    )
    data = {
        "title": "A title",
        "content": "Some content",
        "type": type,
        "action_title": action_title,
        "action_url": action_url,
        **admin_field_split_dt("publication_date", publication_date),
    }
    if expiration_date is not None:
        data.update(admin_field_split_dt("expiration_date", expiration_date))
    return data


def test_content_field_uses_martor_editor():
    form = FeedItemAdminForm()
    assert isinstance(form.fields["content"].widget, AdminMartorWidget)


def test_form_requires_action_fields_for_call_to_action():
    form = FeedItemAdminForm(data=_base_form_data(type=FeedItemType.CALL_TO_ACTION))

    assert not form.is_valid()
    assert "action_title" in form.errors
    assert "action_url" in form.errors


def test_form_rejects_expiration_before_publication():
    now = aware_utcnow().replace(microsecond=0, second=0)
    form = FeedItemAdminForm(
        data=_base_form_data(
            publication_date=now,
            expiration_date=now - timedelta(days=1),
        )
    )

    assert not form.is_valid()
    assert "expiration_date" in form.errors


def test_form_rejects_second_active_release_naming_existing(empty_feed_items):
    f.FeedItemFactory.create(
        type=FeedItemType.RELEASE,
        title="Current release",
        expiration_date=None,
    )

    form = FeedItemAdminForm(data=_base_form_data(type=FeedItemType.RELEASE))

    assert not form.is_valid()
    assert "Current release" in str(form.errors)


def test_form_rejects_overlapping_maintenance_naming_conflict():
    base = aware_utcnow().replace(microsecond=0, second=0)
    f.FeedItemFactory.create(
        type=FeedItemType.MAINTENANCE,
        title="Maintenance A",
        publication_date=base,
        expiration_date=base + timedelta(days=5),
    )

    form = FeedItemAdminForm(
        data=_base_form_data(
            type=FeedItemType.MAINTENANCE,
            publication_date=base + timedelta(days=2),
            expiration_date=base + timedelta(days=8),
        )
    )

    assert not form.is_valid()
    assert "Maintenance A" in str(form.errors)


def test_form_accepts_disjoint_maintenance():
    base = aware_utcnow().replace(microsecond=0, second=0)
    f.FeedItemFactory.create(
        type=FeedItemType.MAINTENANCE,
        title="Maintenance A",
        publication_date=base,
        expiration_date=base + timedelta(days=5),
    )

    form = FeedItemAdminForm(
        data=_base_form_data(
            type=FeedItemType.MAINTENANCE,
            publication_date=base + timedelta(days=6),
            expiration_date=base + timedelta(days=8),
        )
    )

    assert form.is_valid(), form.errors


def test_form_save_assembles_active_period_from_the_two_date_fields():
    base = aware_utcnow().replace(microsecond=0, second=0)
    form = FeedItemAdminForm(
        data=_base_form_data(
            type=FeedItemType.MAINTENANCE,
            publication_date=base,
            expiration_date=base + timedelta(days=2),
        )
    )

    assert form.is_valid(), form.errors
    item = form.save()
    item.refresh_from_db()

    assert item.publication_date == base
    assert item.expiration_date == base + timedelta(days=2)
