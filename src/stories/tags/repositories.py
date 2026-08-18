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

from uuid import UUID

from django.db.models import Count
from django.db.models.functions import Lower

from projects.projects.models import Project
from stories.stories.models import Story
from stories.tags.models import StoryTag, StoryTagAssignment, StoryTagWithCount

##########################################################
# create story tag
##########################################################


async def create_story_tag(
    project: Project, label: str, color: int
) -> StoryTagWithCount:
    story_tag = await StoryTag.objects.acreate(
        project=project, label=label, color=color
    )
    story_tag.stories_count = 0
    return story_tag


##########################################################
# list story tags
##########################################################


async def list_story_tags(project_id: UUID) -> list[StoryTagWithCount]:
    return [
        tag
        async for tag in StoryTag.objects.filter(project_id=project_id)
        .annotate(stories_count=Count("stories"))
        .order_by(Lower("label"))
    ]


##########################################################
# get story tag
##########################################################


async def get_story_tag(story_tag_id: UUID) -> StoryTagWithCount:
    return (
        await StoryTag.objects.select_related("project")
        .annotate(stories_count=Count("stories"))
        .aget(id=story_tag_id)
    )


##########################################################
# update story tag
##########################################################


async def add_or_update_stories_count(
    story_tag: StoryTag | StoryTagWithCount,
) -> StoryTagWithCount:
    story_tag.stories_count = await story_tag.stories.acount()
    return story_tag


async def update_story_tag(
    story_tag: StoryTagWithCount, values: dict
) -> StoryTagWithCount:
    for attr, value in values.items():
        setattr(story_tag, attr, value)

    await story_tag.asave()
    return story_tag


##########################################################
# delete story tag
##########################################################


async def delete_story_tag(story_tag: StoryTag) -> int:
    num_deleted, _ = await StoryTag.objects.filter(id=story_tag.id).adelete()
    return num_deleted


##########################################################
# story tag assignments
##########################################################


async def create_story_tag_assignment(
    story: Story, tag: StoryTag
) -> tuple[StoryTagAssignment, bool]:
    (
        story_tag_assignment,
        created,
    ) = await StoryTagAssignment.objects.aget_or_create(story=story, tag=tag)
    story_tag_assignment.story = story
    story_tag_assignment.tag = tag
    return story_tag_assignment, created


async def get_story_tag_assignment(story_id: UUID, tag_id: UUID) -> StoryTagAssignment:
    return await StoryTagAssignment.objects.select_related(
        "story", "story__project", "tag"
    ).aget(story_id=story_id, tag_id=tag_id)


async def delete_story_tag_assignment(
    story_tag_assignment: StoryTagAssignment,
) -> None:
    await StoryTagAssignment.objects.filter(id=story_tag_assignment.id).adelete()


##########################################################
# misc story tag
##########################################################


async def count_story_tags(project_id: UUID) -> int:
    return await StoryTag.objects.filter(project_id=project_id).acount()
