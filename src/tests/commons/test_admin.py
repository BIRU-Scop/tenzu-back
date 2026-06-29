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

import pytest
from django.contrib.admin import site
from django.urls import reverse

from tests.utils import factories as f


def test_feeditem_admin_is_registered_and_mounted():
    assert reverse("admin:feeds_feeditem_changelist")


def test_restrict_admin_registry_keeps_only_whitelist():
    from django.contrib.admin import AdminSite

    from configurations.utils import restrict_admin_registry
    from feeds.models import FeedItem, FeedItemReadStatus

    test_site = AdminSite()
    test_site.register(FeedItem)
    test_site.register(FeedItemReadStatus)

    unregistered = restrict_admin_registry(test_site, ["feeds.FeedItem"])

    assert {m._meta.label for m in test_site._registry} == {"feeds.FeedItem"}
    assert unregistered == ["feeds.FeedItemReadStatus"]


##########################################################
# Superuser-only access
##########################################################


@pytest.mark.django_db()
def test_admin_permission_granted_to_superuser(rf):
    user = f.UserFactory.create(is_superuser=True)
    request = rf.get("/admin/")
    request.user = user

    assert site.has_permission(request) is True


@pytest.mark.django_db()
def test_admin_permission_denied_to_non_superuser(rf):
    user = f.UserFactory.create(is_superuser=False)
    request = rf.get("/admin/")
    request.user = user

    assert site.has_permission(request) is False
