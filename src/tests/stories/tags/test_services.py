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

from types import SimpleNamespace
from unittest.mock import patch

import pytest
from django.db import IntegrityError
from django.test import override_settings
from psycopg import errors as pg_errors

from stories.tags import models, services
from stories.tags.services import exceptions as ex
from tests.utils import factories as f
from tests.utils.utils import patch_db_transaction


def _build_integrity_error(constraint_name: str) -> IntegrityError:
    class _FakeDiagUniqueViolation(pg_errors.UniqueViolation):
        @property
        def diag(self):
            return SimpleNamespace(constraint_name=constraint_name)

    integrity_error = IntegrityError("duplicate key value violates unique constraint")
    integrity_error.__cause__ = _FakeDiagUniqueViolation()
    return integrity_error


##########################################################
# update_story_tag
##########################################################


async def test_update_story_tag_translates_unique_integrity_error():
    project = f.build_project()
    tag = f.build_story_tag(project=project, label="Feature")

    with (
        patch(
            "stories.tags.services.story_tags_repositories", autospec=True
        ) as fake_repo,
        patch("stories.tags.services.story_tags_events", autospec=True) as fake_events,
        patch_db_transaction(),
        pytest.raises(ex.StoryTagLabelAlreadyExists),
    ):
        fake_repo.update_story_tag.side_effect = _build_integrity_error(
            models.UNIQUE_LABEL_CONSTRAINT
        )

        await services.update_story_tag(story_tag=tag, values={"label": "bug"})

    fake_events.emit_event_when_story_tag_is_updated.assert_not_awaited()


async def test_update_story_tag_emits_event():
    project = f.build_project()
    tag = f.build_story_tag(project=project, label="Bug", color=3)

    with (
        patch(
            "stories.tags.services.story_tags_repositories", autospec=True
        ) as fake_repo,
        patch("stories.tags.services.story_tags_events", autospec=True) as fake_events,
        patch_db_transaction(),
    ):
        fake_repo.update_story_tag.return_value = tag

        story_tag = await services.update_story_tag(
            story_tag=tag, values={"label": "Bug"}
        )

    assert story_tag is tag
    fake_events.emit_event_when_story_tag_is_updated.assert_awaited_once_with(
        story_tag=tag
    )


##########################################################
# delete_story_tag
##########################################################


async def test_delete_story_tag_emits_event():
    project = f.build_project()
    tag = f.build_story_tag(project=project, label="Bug")

    with (
        patch(
            "stories.tags.services.story_tags_repositories", autospec=True
        ) as fake_repo,
        patch("stories.tags.services.story_tags_events", autospec=True) as fake_events,
    ):
        fake_repo.delete_story_tag.return_value = 1

        await services.delete_story_tag(story_tag=tag)

    fake_repo.delete_story_tag.assert_awaited_once_with(story_tag=tag)
    fake_events.emit_event_when_story_tag_is_deleted.assert_awaited_once_with(
        story_tag=tag
    )


async def test_delete_story_tag_already_deleted_does_not_emit_event():
    project = f.build_project()
    tag = f.build_story_tag(project=project, label="Bug")

    with (
        patch(
            "stories.tags.services.story_tags_repositories", autospec=True
        ) as fake_repo,
        patch("stories.tags.services.story_tags_events", autospec=True) as fake_events,
    ):
        fake_repo.delete_story_tag.return_value = 0

        await services.delete_story_tag(story_tag=tag)

    fake_events.emit_event_when_story_tag_is_deleted.assert_not_awaited()


##########################################################
# create_story_tag_assignment / delete_story_tag_assignment
##########################################################


async def test_create_story_tag_assignment_emits_event_when_created():
    project = f.build_project()
    story = f.build_story(project=project)
    tag = f.build_story_tag(project=project, label="Bug")
    assignment = f.build_story_tag_assignment(story=story, tag=tag)

    with (
        patch(
            "stories.tags.services.story_tags_repositories", autospec=True
        ) as fake_repo,
        patch("stories.tags.services.story_tags_events", autospec=True) as fake_events,
    ):
        fake_repo.create_story_tag_assignment.return_value = (assignment, True)

        def side_effect(tag):
            tag.stories_count = 1

        fake_repo.add_or_update_stories_count.side_effect = side_effect

        result = await services.create_story_tag_assignment(story=story, tag=tag)

    assert result is assignment
    assert result.tag is tag
    assert result.tag.stories_count == 1
    fake_events.emit_event_when_story_tag_assignment_is_created.assert_awaited_once_with(
        story_tag_assignment=assignment
    )
    fake_events.emit_event_when_story_tag_is_updated.assert_awaited_once_with(
        story_tag=result.tag
    )


async def test_create_story_tag_assignment_noop_does_not_emit_event():
    project = f.build_project()
    story = f.build_story(project=project)
    tag = f.build_story_tag(project=project, label="Bug")
    assignment = f.build_story_tag_assignment(story=story, tag=tag)

    with (
        patch(
            "stories.tags.services.story_tags_repositories", autospec=True
        ) as fake_repo,
        patch("stories.tags.services.story_tags_events", autospec=True) as fake_events,
    ):
        fake_repo.create_story_tag_assignment.return_value = (assignment, False)

        result = await services.create_story_tag_assignment(story=story, tag=tag)

    assert result is assignment
    fake_events.emit_event_when_story_tag_assignment_is_created.assert_not_awaited()
    fake_events.emit_event_when_story_tag_is_updated.assert_not_awaited()


async def test_create_story_tag_assignment_cross_project_error():
    story = f.build_story(project=f.build_project())
    tag = f.build_story_tag(project=f.build_project(), label="Bug")

    with (
        patch(
            "stories.tags.services.story_tags_repositories", autospec=True
        ) as fake_repo,
        patch("stories.tags.services.story_tags_events", autospec=True) as fake_events,
        pytest.raises(ex.InvalidStoryTagAssignment),
    ):
        await services.create_story_tag_assignment(story=story, tag=tag)

    fake_repo.create_story_tag_assignment.assert_not_awaited()
    fake_events.emit_event_when_story_tag_assignment_is_created.assert_not_awaited()


async def test_delete_story_tag_assignment_emits_event():
    project = f.build_project()
    story = f.build_story(project=project)
    tag = f.build_story_tag(project=project, label="Bug")
    assignment = f.build_story_tag_assignment(story=story, tag=tag)

    with (
        patch(
            "stories.tags.services.story_tags_repositories", autospec=True
        ) as fake_repo,
        patch("stories.tags.services.story_tags_events", autospec=True) as fake_events,
    ):
        fresh_tag = f.build_story_tag(project=project, label="Bug")
        fake_repo.get_story_tag.return_value = fresh_tag

        await services.delete_story_tag_assignment(story_tag_assignment=assignment)

    fake_repo.delete_story_tag_assignment.assert_awaited_once_with(
        story_tag_assignment=assignment
    )
    fake_events.emit_event_when_story_tag_assignment_is_deleted.assert_awaited_once_with(
        story_tag_assignment=assignment
    )
    fake_repo.get_story_tag.assert_awaited_once_with(story_tag_id=tag.id)
    fake_events.emit_event_when_story_tag_is_updated.assert_awaited_once_with(
        story_tag=fresh_tag
    )


##########################################################
# create_story_tag
##########################################################


async def test_create_story_tag_translates_unique_integrity_error():
    project = f.build_project()

    with (
        patch(
            "stories.tags.services.story_tags_repositories", autospec=True
        ) as fake_repo,
        patch_db_transaction(),
        pytest.raises(ex.StoryTagLabelAlreadyExists),
    ):
        fake_repo.count_story_tags.return_value = 0
        fake_repo.create_story_tag.side_effect = _build_integrity_error(
            models.UNIQUE_LABEL_CONSTRAINT
        )

        await services.create_story_tag(project=project, label="bug", color=1)


async def test_create_story_tag_reraises_other_integrity_error():
    project = f.build_project()

    fk_error = IntegrityError("violates foreign key constraint")
    fk_error.__cause__ = pg_errors.ForeignKeyViolation()

    with (
        patch(
            "stories.tags.services.story_tags_repositories", autospec=True
        ) as fake_repo,
        patch_db_transaction(),
        pytest.raises(IntegrityError) as exc_info,
    ):
        fake_repo.count_story_tags.return_value = 0
        fake_repo.create_story_tag.side_effect = fk_error

        await services.create_story_tag(project=project, label="bug", color=1)
    assert exc_info.value is fk_error

    other_unique_error = _build_integrity_error("some_other_unique_constraint")

    with (
        patch(
            "stories.tags.services.story_tags_repositories", autospec=True
        ) as fake_repo,
        patch_db_transaction(),
        pytest.raises(IntegrityError) as exc_info,
    ):
        fake_repo.count_story_tags.return_value = 0
        fake_repo.create_story_tag.side_effect = other_unique_error

        await services.create_story_tag(project=project, label="bug", color=1)
    assert exc_info.value is other_unique_error


async def test_create_story_tag_max_per_project_reached():
    project = f.build_project()

    with (
        patch(
            "stories.tags.services.story_tags_repositories", autospec=True
        ) as fake_repo,
        override_settings(**{"MAX_STORY_TAGS_PER_PROJECT": 2}),
        pytest.raises(ex.MaxStoryTagsPerProjectReached),
    ):
        fake_repo.count_story_tags.return_value = 2

        await services.create_story_tag(project=project, label="bug", color=1)

    fake_repo.create_story_tag.assert_not_awaited()


async def test_create_story_tag_emits_event():
    project = f.build_project()
    tag = f.build_story_tag(project=project, label="Bug", color=3)

    with (
        patch(
            "stories.tags.services.story_tags_repositories", autospec=True
        ) as fake_repo,
        patch("stories.tags.services.story_tags_events", autospec=True) as fake_events,
        patch_db_transaction(),
    ):
        fake_repo.count_story_tags.return_value = 0
        fake_repo.create_story_tag.return_value = tag

        story_tag = await services.create_story_tag(
            project=project, label="Bug", color=3
        )

    assert story_tag is tag
    fake_events.emit_event_when_story_tag_is_created.assert_awaited_once_with(
        story_tag=tag
    )
