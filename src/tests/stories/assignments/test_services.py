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

from unittest.mock import patch

import pytest

from projects.memberships.models import ProjectMembership
from stories.assignments import services
from stories.assignments.services import exceptions as ex
from tests.utils import factories as f

#######################################################
# create_story_assignment
#######################################################


async def test_create_story_assignment_user_without_permission():
    user = f.build_user()
    project = f.build_project()
    role = f.build_project_role(project=project, permissions=[], is_owner=False)
    f.build_project_membership(user=user, project=project, role=role)
    story = f.build_story(project=project)
    f.build_story_assignment(story=story, user=user)

    with (
        patch(
            "stories.assignments.services.pj_memberships_repositories", autospec=True
        ) as fake_pj_memberships_repo,
        patch(
            "stories.assignments.services.story_assignments_repositories", autospec=True
        ) as fake_story_assignment_repo,
        patch(
            "stories.assignments.services.stories_assignments_events", autospec=True
        ) as fake_stories_assignments_events,
        patch(
            "stories.assignments.services.stories_assignments_notifications",
            autospec=True,
        ) as fake_stories_assignments_notifications,
        pytest.raises(ex.InvalidAssignmentError),
    ):
        fake_pj_memberships_repo.get_membership.side_effect = (
            ProjectMembership.DoesNotExist
        )

        await services.create_story_assignment(
            project_id=story.project.id,
            story=story,
            user_id=user.username,
            created_by=story.created_by,
        )
        fake_story_assignment_repo.create_story_assignment.assert_not_awaited()
        fake_stories_assignments_events.emit_event_when_story_assignment_is_created.assert_not_awaited()
        fake_stories_assignments_notifications.notify_when_story_is_assigned.assert_not_awaited()


async def test_create_story_assignment_ok():
    user = f.build_user()
    project = f.build_project()
    role = f.build_project_role(project=project)
    membership = f.build_project_membership(user=user, project=project, role=role)
    story = f.build_story(project=project)
    story_assignment = f.build_story_assignment(story=story, user=user)

    with (
        patch(
            "stories.assignments.services.pj_memberships_repositories", autospec=True
        ) as fake_pj_memberships_repo,
        patch(
            "stories.assignments.services.story_assignments_repositories", autospec=True
        ) as fake_story_assignment_repo,
        patch(
            "stories.assignments.services.stories_assignments_events", autospec=True
        ) as fake_stories_assignments_events,
        patch(
            "stories.assignments.services.stories_assignments_notifications",
            autospec=True,
        ) as fake_stories_assignments_notifications,
    ):
        fake_pj_memberships_repo.get_membership.return_value = membership
        fake_story_assignment_repo.create_story_assignment.return_value = (
            story_assignment,
            True,
        )

        await services.create_story_assignment(
            project_id=project.id,
            story=story,
            user_id=user.id,
            created_by=story.created_by,
        )
        fake_story_assignment_repo.create_story_assignment.assert_awaited_once_with(
            story=story,
            user=user,
        )
        fake_stories_assignments_events.emit_event_when_story_assignment_is_created.assert_awaited_once_with(
            story_assignment=story_assignment
        )
        fake_stories_assignments_notifications.notify_when_story_is_assigned.assert_awaited_once_with(
            story=story, assigned_to=user, emitted_by=story.created_by
        )


async def test_create_story_assignment_already_assignment():
    user = f.build_user()
    project = f.build_project()
    role = f.build_project_role(project=project)
    membership = f.build_project_membership(user=user, project=project, role=role)
    story = f.build_story(project=project)
    story_assignment = f.build_story_assignment(story=story, user=user)

    with (
        patch(
            "stories.assignments.services.pj_memberships_repositories", autospec=True
        ) as fake_pj_memberships_repo,
        patch(
            "stories.assignments.services.story_assignments_repositories", autospec=True
        ) as fake_story_assignment_repo,
        patch(
            "stories.assignments.services.stories_assignments_events", autospec=True
        ) as fake_stories_assignments_events,
        patch(
            "stories.assignments.services.stories_assignments_notifications",
            autospec=True,
        ) as fake_stories_assignments_notifications,
    ):
        fake_pj_memberships_repo.get_membership.return_value = membership
        fake_story_assignment_repo.create_story_assignment.return_value = (
            story_assignment,
            True,
        )

        await services.create_story_assignment(
            project_id=project.id,
            story=story,
            user_id=user.id,
            created_by=story.created_by,
        )

        fake_story_assignment_repo.create_story_assignment.return_value = (
            story_assignment,
            False,
        )

        await services.create_story_assignment(
            project_id=project.id,
            story=story,
            user_id=user.id,
            created_by=story.created_by,
        )
        fake_story_assignment_repo.create_story_assignment.assert_awaited_with(
            story=story,
            user=user,
        )
        fake_stories_assignments_events.emit_event_when_story_assignment_is_created.assert_awaited_once_with(
            story_assignment=story_assignment
        )
        fake_stories_assignments_notifications.notify_when_story_is_assigned.assert_awaited_once_with(
            story=story, assigned_to=user, emitted_by=story.created_by
        )


#######################################################
# get_story_assignment
#######################################################


async def test_get_story_assignment():
    user = f.build_user()
    story = f.build_story()
    story_assignment = f.build_story_assignment(story=story, user=user)

    with (
        patch(
            "stories.assignments.services.story_assignments_repositories", autospec=True
        ) as fake_story_assignment_repo,
    ):
        fake_story_assignment_repo.get_story_assignment.return_value = story_assignment

        await services.get_story_assignment(
            project_id=story.project.id, ref=story.ref, user_id=user.id
        )

        fake_story_assignment_repo.get_story_assignment.assert_awaited_once_with(
            filters={
                "project_id": story.project.id,
                "ref": story.ref,
                "user_id": user.id,
            },
            select_related=["story", "user", "project"],
        )


#######################################################
# delete_story_assignment
#######################################################


async def test_delete_story_assignment_fail():
    user = f.build_user()
    story = f.build_story()
    story_assignment = f.build_story_assignment(story=story, user=user)

    with (
        patch(
            "stories.assignments.services.story_assignments_repositories", autospec=True
        ) as fake_story_assignment_repo,
        patch(
            "stories.assignments.services.stories_assignments_events", autospec=True
        ) as fake_stories_assignments_events,
        patch(
            "stories.assignments.services.stories_assignments_notifications",
            autospec=True,
        ) as fake_stories_assignments_notifications,
    ):
        fake_story_assignment_repo.delete_stories_assignments.return_value = 0

        await services.delete_story_assignment(
            story_assignment=story_assignment, deleted_by=story.created_by
        )
        fake_story_assignment_repo.delete_stories_assignments.assert_awaited_once_with(
            filters={"id": story_assignment.id},
        )
        fake_stories_assignments_events.emit_event_when_story_assignment_is_deleted.assert_not_awaited()
        fake_stories_assignments_notifications.notify_when_story_is_unassigned.assert_not_awaited()


async def test_delete_story_assignment_ok():
    user = f.build_user()
    story = f.build_story()
    story_assignment = f.build_story_assignment(story=story, user=user)

    with (
        patch(
            "stories.assignments.services.story_assignments_repositories", autospec=True
        ) as fake_story_assignment_repo,
        patch(
            "stories.assignments.services.stories_assignments_events", autospec=True
        ) as fake_stories_assignments_events,
        patch(
            "stories.assignments.services.stories_assignments_notifications",
            autospec=True,
        ) as fake_stories_assignments_notifications,
    ):
        fake_story_assignment_repo.delete_stories_assignments.return_value = 1

        await services.delete_story_assignment(
            story_assignment=story_assignment, deleted_by=story.created_by
        )
        fake_story_assignment_repo.delete_stories_assignments.assert_awaited_once_with(
            filters={"id": story_assignment.id},
        )
        fake_stories_assignments_events.emit_event_when_story_assignment_is_deleted.assert_awaited_once_with(
            story_assignment=story_assignment
        )
        fake_stories_assignments_notifications.notify_when_story_is_unassigned.assert_awaited_once_with(
            story=story, unassigned_to=user, emitted_by=story.created_by
        )
