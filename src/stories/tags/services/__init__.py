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

from django.conf import settings
from django.db import IntegrityError
from psycopg import errors as pg_errors

from commons.utils import transaction_atomic_async
from projects.projects.models import Project
from stories.tags import events as story_tags_events
from stories.tags import repositories as story_tags_repositories
from stories.tags.models import (
    UNIQUE_LABEL_CONSTRAINT,
    StoryTag,
    StoryTagAssignment,
    StoryTagWithCount,
)
from stories.tags.services import exceptions as ex


def _is_unique_label_violation(error: IntegrityError) -> bool:
    cause = error.__cause__
    if not isinstance(cause, pg_errors.UniqueViolation):
        return False
    return cause.diag.constraint_name == UNIQUE_LABEL_CONSTRAINT


##########################################################
# create story tag
##########################################################


async def create_story_tag(
    project: Project, label: str, color: int
) -> StoryTagWithCount:
    num_tags = await story_tags_repositories.count_story_tags(project_id=project.id)
    if num_tags >= settings.MAX_STORY_TAGS_PER_PROJECT:
        raise ex.MaxStoryTagsPerProjectReached(
            "Maximum number of tags for this project is reached"
        )

    try:
        async with transaction_atomic_async():
            story_tag = await story_tags_repositories.create_story_tag(
                project=project, label=label, color=color
            )
    except IntegrityError as e:
        if _is_unique_label_violation(e):
            raise ex.StoryTagLabelAlreadyExists(
                f"A tag with the label {label!r} already exists in this project"
            ) from e
        raise

    await story_tags_events.emit_event_when_story_tag_is_created(story_tag=story_tag)

    return story_tag


##########################################################
# update story tag
##########################################################


async def update_story_tag(
    story_tag: StoryTagWithCount, values: dict
) -> StoryTagWithCount:
    try:
        async with transaction_atomic_async():
            updated_story_tag = await story_tags_repositories.update_story_tag(
                story_tag=story_tag, values=values
            )
    except IntegrityError as e:
        if _is_unique_label_violation(e):
            raise ex.StoryTagLabelAlreadyExists(
                f"A tag with the label {values.get('label')!r} already exists"
                " in this project"
            ) from e
        raise

    await story_tags_events.emit_event_when_story_tag_is_updated(
        story_tag=updated_story_tag
    )

    return updated_story_tag


##########################################################
# delete story tag
##########################################################


async def delete_story_tag(story_tag: StoryTag) -> None:
    num_deleted = await story_tags_repositories.delete_story_tag(story_tag=story_tag)
    if num_deleted:
        await story_tags_events.emit_event_when_story_tag_is_deleted(
            story_tag=story_tag
        )


##########################################################
# story tag assignments
##########################################################


async def create_story_tag_assignment(story, tag: StoryTag) -> StoryTagAssignment:
    if tag.project_id != story.project_id:
        raise ex.InvalidStoryTagAssignment(
            "The tag does not belong to the story's project"
        )

    (
        story_tag_assignment,
        created,
    ) = await story_tags_repositories.create_story_tag_assignment(story=story, tag=tag)
    if created:
        # refresh the stories count annotation for the tag with a new request in order to handle concurrent creation
        await story_tags_repositories.add_or_update_stories_count(
            story_tag_assignment.tag
        )

        await story_tags_events.emit_event_when_story_tag_assignment_is_created(
            story_tag_assignment=story_tag_assignment
        )
        await story_tags_events.emit_event_when_story_tag_is_updated(
            story_tag=story_tag_assignment.tag
        )

    return story_tag_assignment


async def delete_story_tag_assignment(
    story_tag_assignment: StoryTagAssignment,
) -> None:
    tag = story_tag_assignment.tag
    await story_tags_repositories.delete_story_tag_assignment(
        story_tag_assignment=story_tag_assignment
    )
    fresh_tag = await story_tags_repositories.get_story_tag(story_tag_id=tag.id)
    story_tag_assignment.tag = fresh_tag
    await story_tags_events.emit_event_when_story_tag_assignment_is_deleted(
        story_tag_assignment=story_tag_assignment
    )
    await story_tags_events.emit_event_when_story_tag_is_updated(story_tag=fresh_tag)
    return None


##########################################################
# list story tags
##########################################################


async def list_story_tags(project_id: UUID) -> list[StoryTagWithCount]:
    return await story_tags_repositories.list_story_tags(project_id=project_id)
