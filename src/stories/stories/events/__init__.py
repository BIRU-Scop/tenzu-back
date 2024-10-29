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
from projects.projects.models import Project
from stories.stories.events.content import (
    CreateStoryContent,
    DeleteStoryContent,
    ReorderStoriesContent,
    UpdateStoryContent,
)
from stories.stories.serializers import ReorderStoriesSerializer, StoryDetailSerializer
from users.models import AnyUser

CREATE_STORY = "stories.create"
UPDATE_STORY = "stories.update"
REORDER_STORIES = "stories.reorder"
DELETE_STORY = "stories.delete"


async def emit_event_when_story_is_created(project: Project, story: StoryDetailSerializer) -> None:
    await events_manager.publish_on_project_channel(
        project=project,
        type=CREATE_STORY,
        content=CreateStoryContent(story=story),
    )


async def emit_event_when_story_is_updated(
    project: Project, story: StoryDetailSerializer, updates_attrs: list[str]
) -> None:
    await events_manager.publish_on_project_channel(
        project=project,
        type=UPDATE_STORY,
        content=UpdateStoryContent(
            story=story,
            updates_attrs=updates_attrs,
        ),
    )


async def emit_when_stories_are_reordered(project: Project, reorder: ReorderStoriesSerializer) -> None:
    await events_manager.publish_on_project_channel(
        project=project,
        type=REORDER_STORIES,
        content=ReorderStoriesContent(reorder=reorder),
    )


async def emit_event_when_story_is_deleted(project: Project, ref: int, deleted_by: AnyUser) -> None:
    await events_manager.publish_on_project_channel(
        project=project,
        type=DELETE_STORY,
        content=DeleteStoryContent(ref=ref, deleted_by=deleted_by),
    )
