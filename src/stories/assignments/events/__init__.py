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

from events import events_manager
from stories.assignments.events.content import (
    CreateStoryAssignmentContent,
    DeleteStoryAssignmentContent,
)
from stories.assignments.models import StoryAssignment
from stories.assignments.serializers import StoryAssignmentSerializer

CREATE_STORY_ASSIGNMENT = "storiesassignments.create"
DELETE_STORY_ASSIGNMENT = "storiesassignments.delete"


async def emit_event_when_story_assignment_is_created(
    story_assignment: StoryAssignment,
) -> None:
    await events_manager.publish_on_user_channel(
        user=story_assignment.user,
        type=CREATE_STORY_ASSIGNMENT,
        content=CreateStoryAssignmentContent(
            story_assignment=StoryAssignmentSerializer.from_orm(story_assignment)
        ),
    )

    await events_manager.publish_on_project_channel(
        project=story_assignment.story.project,
        type=CREATE_STORY_ASSIGNMENT,
        content=CreateStoryAssignmentContent(
            story_assignment=StoryAssignmentSerializer.from_orm(story_assignment)
        ),
    )


async def emit_event_when_story_assignment_is_deleted(
    story_assignment: StoryAssignment,
) -> None:
    await events_manager.publish_on_user_channel(
        user=story_assignment.user,
        type=DELETE_STORY_ASSIGNMENT,
        content=DeleteStoryAssignmentContent(
            story_assignment=StoryAssignmentSerializer.from_orm(story_assignment)
        ),
    )

    await events_manager.publish_on_project_channel(
        project=story_assignment.story.project,
        type=DELETE_STORY_ASSIGNMENT,
        content=DeleteStoryAssignmentContent(
            story_assignment=StoryAssignmentSerializer.from_orm(story_assignment)
        ),
    )
