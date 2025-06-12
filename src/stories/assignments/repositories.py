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

from typing import Literal, TypedDict
from uuid import UUID

from stories.assignments.models import StoryAssignment
from stories.stories.models import Story
from users.models import User

##########################################################
# filters and querysets
##########################################################


class StoryAssignmentFilters(TypedDict, total=False):
    id: UUID
    story__ref: int
    story__project_id: UUID
    story__project__workspace_id: UUID
    story_id: UUID
    user_id: UUID
    user__project_memberships__role_id: UUID


StoryAssignmentSelectRelated = list[
    Literal[
        "story",
        "user",
        "story__project",
        "story__project__workspace",
    ]
]


##########################################################
# create story assignment
##########################################################


async def create_story_assignment(
    story: Story, user: User
) -> tuple[StoryAssignment, bool]:
    return await StoryAssignment.objects.aget_or_create(story=story, user=user)


##########################################################
# get story assignment
##########################################################


async def get_story_assignment(
    filters: StoryAssignmentFilters = {},
    select_related: StoryAssignmentSelectRelated = ["story", "user"],
) -> StoryAssignment | None:
    qs = StoryAssignment.objects.all().filter(**filters).select_related(*select_related)
    return await qs.aget()


##########################################################
# delete story assignment
##########################################################


async def delete_stories_assignments(filters: StoryAssignmentFilters = {}) -> int:
    qs = StoryAssignment.objects.all().filter(**filters)
    count, _ = await qs.adelete()
    return count
