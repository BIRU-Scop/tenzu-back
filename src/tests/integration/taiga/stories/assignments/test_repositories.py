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

import pytest

from stories.assignments import repositories
from tests.utils import factories as f

pytestmark = pytest.mark.django_db


##########################################################
# create_story_assignment
##########################################################


async def test_create_story_assignment_ok() -> None:
    user = await f.create_user()
    story = await f.create_story()

    story_assignment, created = await repositories.create_story_assignment(story=story, user=user)

    assert story_assignment.user == user
    assert story_assignment.story == story


##########################################################
# get_story_assignment
##########################################################


async def test_get_story_assignment() -> None:
    story_assignment = await f.create_story_assignment()
    story_assignment_test = await repositories.get_story_assignment(
        filters={
            "project_id": story_assignment.story.project_id,
            "ref": story_assignment.story.ref,
            "username": story_assignment.user.username,
        },
        select_related=["story", "user", "project"],
    )
    assert story_assignment.user.username == story_assignment_test.user.username
    assert story_assignment.story.id == story_assignment_test.story.id


##########################################################
# delete_stories_assignments
##########################################################


async def test_delete_stories_assignments() -> None:
    story_assignment = await f.create_story_assignment()
    deleted = await repositories.delete_stories_assignments(
        filters={
            "story_id": story_assignment.story.id,
            "username": story_assignment.user.username,
        },
    )
    assert deleted == 1
