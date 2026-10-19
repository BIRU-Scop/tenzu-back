# -*- coding: utf-8 -*-
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

from events import events_manager
from stories.tags.events.content import (
    CreateStoryTagAssignmentContent,
    CreateStoryTagContent,
    DeleteStoryTagAssignmentContent,
    DeleteStoryTagContent,
    UpdateStoryTagContent,
)
from stories.tags.models import StoryTagAssignment, StoryTagWithCount
from stories.tags.serializers import (
    StoryTagAssignmentSerializer,
    StoryTagWithCountSerializer,
)

CREATE_STORY_TAG = "storiestags.create"
UPDATE_STORY_TAG = "storiestags.update"
DELETE_STORY_TAG = "storiestags.delete"
CREATE_STORY_TAG_ASSIGNMENT = "storiestagsassignments.create"
DELETE_STORY_TAG_ASSIGNMENT = "storiestagsassignments.delete"


async def emit_event_when_story_tag_is_created(story_tag: StoryTagWithCount) -> None:
    await events_manager.publish_on_project_channel(
        project=story_tag.project,
        type=CREATE_STORY_TAG,
        content=CreateStoryTagContent(
            story_tag=StoryTagWithCountSerializer.model_validate(story_tag)
        ),
    )


async def emit_event_when_story_tag_is_updated(story_tag: StoryTagWithCount) -> None:
    await events_manager.publish_on_project_channel(
        project=story_tag.project,
        type=UPDATE_STORY_TAG,
        content=UpdateStoryTagContent(
            story_tag=StoryTagWithCountSerializer.model_validate(story_tag)
        ),
    )


async def emit_event_when_story_tag_is_deleted(story_tag: StoryTagWithCount) -> None:
    await events_manager.publish_on_project_channel(
        project=story_tag.project,
        type=DELETE_STORY_TAG,
        content=DeleteStoryTagContent(
            story_tag=StoryTagWithCountSerializer.model_validate(story_tag)
        ),
    )


async def emit_event_when_story_tag_assignment_is_created(
    story_tag_assignment: StoryTagAssignment,
) -> None:
    await events_manager.publish_on_project_channel(
        project=story_tag_assignment.story.project,
        type=CREATE_STORY_TAG_ASSIGNMENT,
        content=CreateStoryTagAssignmentContent(
            story_tag_assignment=StoryTagAssignmentSerializer.model_validate(
                story_tag_assignment
            )
        ),
    )


async def emit_event_when_story_tag_assignment_is_deleted(
    story_tag_assignment: StoryTagAssignment,
) -> None:
    await events_manager.publish_on_project_channel(
        project=story_tag_assignment.story.project,
        type=DELETE_STORY_TAG_ASSIGNMENT,
        content=DeleteStoryTagAssignmentContent(
            story_tag_assignment=StoryTagAssignmentSerializer.model_validate(
                story_tag_assignment
            )
        ),
    )
