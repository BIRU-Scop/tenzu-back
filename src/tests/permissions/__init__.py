# -*- coding: utf-8 -*-
# Copyright (C) 2024 BIRU
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

from dataclasses import dataclass

import pytest
from django.contrib.auth.models import AnonymousUser

from permissions import IsRelatedToTheUser
from tests.utils import factories as f

pytestmark = pytest.mark.django_db


#####################################################
# IsRelatedToTheUser
#####################################################


async def test_is_related_to_the_user_with_default_field():
    user1 = f.build_user()
    user2 = f.build_user()
    membership = f.build_project_membership(user=user1)
    assert await IsRelatedToTheUser().is_authorized(user1, membership) is True
    assert await IsRelatedToTheUser().is_authorized(user2, membership) is False


async def test_is_related_to_the_user_with_custom_field():
    user1 = f.build_user()
    user2 = f.build_user()
    story = f.build_story(created_by=user1)
    assert await IsRelatedToTheUser("created_by").is_authorized(user1, story) is True
    assert await IsRelatedToTheUser("created_by").is_authorized(user2, story) is False


async def test_is_related_to_the_user_with_anonymous_user():
    @dataclass
    class Obj:
        user: AnonymousUser

    user = AnonymousUser()
    obj = Obj(user=user)
    assert await IsRelatedToTheUser().is_authorized(user, obj) is False
