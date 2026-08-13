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

import pytest
from django.db import IntegrityError
from psycopg import errors as pg_errors

from commons.colors import NUM_COLORS
from commons.utils import transaction_atomic_async
from stories.tags import repositories
from stories.tags.models import UNIQUE_LABEL_CONSTRAINT, StoryTag, StoryTagAssignment
from tests.utils import factories as f

pytestmark = pytest.mark.django_db


##########################################################
# create / list story tags
##########################################################


async def test_create_story_tag(project_template):
    project = await f.create_project(project_template)

    story_tag = await repositories.create_story_tag(
        project=project, label="Bug", color=3
    )

    assert story_tag.id
    assert story_tag.label == "Bug"
    assert story_tag.color == 3
    assert story_tag.project == project
    assert await StoryTag.objects.filter(id=story_tag.id).aexists()


async def test_list_story_tags_sorted_with_count(project_template):
    project = await f.create_project(project_template)
    tag_apple = await f.create_story_tag(project=project, label="apple")
    await f.create_story_tag(project=project, label="Zebra")
    story = await f.create_story(project=project)
    await f.create_story_tag_assignment(tag=tag_apple, story=story)
    await f.create_story_tag(label="apple")

    story_tags = await repositories.list_story_tags(project_id=project.id)

    assert [tag.label for tag in story_tags] == ["apple", "Zebra"]
    assert [tag.stories_count for tag in story_tags] == [1, 0]


##########################################################
# get / update / delete story tag
##########################################################


async def test_update_story_tag(project_template):
    project = await f.create_project(project_template)
    story_tag = await f.create_story_tag(project=project, label="Bug", color=1)

    updated = await repositories.update_story_tag(
        story_tag=story_tag, values={"label": "Feature", "color": 5}
    )

    assert updated.label == "Feature"
    assert updated.color == 5
    await story_tag.arefresh_from_db()
    assert story_tag.label == "Feature"
    assert story_tag.color == 5


async def test_delete_story_tag(project_template):
    project = await f.create_project(project_template)
    story_tag = await f.create_story_tag(project=project, label="Bug")

    num_deleted = await repositories.delete_story_tag(story_tag=story_tag)

    assert num_deleted == 1
    assert not await StoryTag.objects.filter(id=story_tag.id).aexists()


async def test_delete_story_tag_already_deleted_returns_zero(project_template):
    project = await f.create_project(project_template)
    story_tag = await f.create_story_tag(project=project, label="Bug")
    await repositories.delete_story_tag(story_tag=story_tag)

    num_deleted = await repositories.delete_story_tag(story_tag=story_tag)

    assert num_deleted == 0


##########################################################
# constraints
##########################################################


async def test_unique_lower_label_per_project_constraint(project_template):
    project = await f.create_project(project_template)
    story_tag = await f.create_story_tag(project=project, label="Bug")

    # same label in another project is allowed
    await f.create_story_tag(label="Bug")

    # updating a tag to another case of its own label is allowed
    story_tag.label = "BUG"
    await story_tag.asave()

    # case-insensitive duplicate in the same project violates the constraint
    with pytest.raises(IntegrityError) as exc_info:
        await StoryTag.objects.acreate(project=project, label="bug", color=1)

    cause = exc_info.value.__cause__
    assert isinstance(cause, pg_errors.UniqueViolation)
    assert cause.diag.constraint_name == UNIQUE_LABEL_CONSTRAINT


async def test_color_check_constraint(project_template):
    project = await f.create_project(project_template)

    for color in (0, NUM_COLORS + 1):
        with pytest.raises(IntegrityError) as exc_info:
            async with transaction_atomic_async():
                await f.create_story_tag(
                    project=project, label=f"tag-{color}", color=color
                )
        assert isinstance(exc_info.value.__cause__, pg_errors.CheckViolation)


##########################################################
# story tag assignments
##########################################################


async def test_create_story_tag_assignment_idempotent(project_template):
    project = await f.create_project(project_template)
    story = await f.create_story(project=project)
    story_tag = await f.create_story_tag(project=project, label="Bug")

    assignment1, created1 = await repositories.create_story_tag_assignment(
        story=story, tag=story_tag
    )
    assignment2, created2 = await repositories.create_story_tag_assignment(
        story=story, tag=story_tag
    )

    assert created1 is True
    assert created2 is False
    assert assignment1.id == assignment2.id
    assert (
        await StoryTagAssignment.objects.filter(story=story, tag=story_tag).acount()
        == 1
    )


async def test_get_story_tag_assignment(project_template):
    project = await f.create_project(project_template)
    story = await f.create_story(project=project)
    story_tag = await f.create_story_tag(project=project, label="Bug")
    other_tag = await f.create_story_tag(project=project, label="Doc")
    assignment = await f.create_story_tag_assignment(tag=story_tag, story=story)

    found = await repositories.get_story_tag_assignment(
        story_id=story.id, tag_id=story_tag.id
    )
    assert found == assignment

    with pytest.raises(StoryTagAssignment.DoesNotExist):
        await repositories.get_story_tag_assignment(
            story_id=story.id, tag_id=other_tag.id
        )


##########################################################
# cascades
##########################################################


async def test_cascades_delete_story_tag_assignments(project_template):
    project = await f.create_project(project_template)
    story = await f.create_story(project=project)

    # deleting the tag deletes its assignments
    tag_bug = await f.create_story_tag(project=project, label="Bug")
    assignment = await f.create_story_tag_assignment(tag=tag_bug, story=story)
    await tag_bug.adelete()
    assert not await StoryTagAssignment.objects.filter(id=assignment.id).aexists()

    # deleting the story deletes its assignments but not the tag itself
    tag_feature = await f.create_story_tag(project=project, label="Feature")
    assignment = await f.create_story_tag_assignment(tag=tag_feature, story=story)
    await story.adelete()
    assert not await StoryTagAssignment.objects.filter(id=assignment.id).aexists()
    assert await StoryTag.objects.filter(id=tag_feature.id).aexists()

    # deleting the project deletes its tags and their assignments
    story = await f.create_story(project=project)
    assignment = await f.create_story_tag_assignment(tag=tag_feature, story=story)
    await project.adelete()
    assert not await StoryTag.objects.filter(id=tag_feature.id).aexists()
    assert not await StoryTagAssignment.objects.filter(id=assignment.id).aexists()
