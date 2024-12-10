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

from uuid import UUID

from projects.memberships import repositories as pj_memberships_repositories
from stories.assignments import events as stories_assignments_events
from stories.assignments import notifications as stories_assignments_notifications
from stories.assignments import repositories as story_assignments_repositories
from stories.assignments.models import StoryAssignment
from stories.assignments.services import exceptions as ex
from stories.stories.models import Story
from users.models import User

##########################################################
# create story assignment
##########################################################


async def create_story_assignment(
    project_id: UUID, story: Story, username: str, created_by: User
) -> StoryAssignment:
    pj_membership = await pj_memberships_repositories.get_project_membership(
        filters={
            "project_id": project_id,
            "username": username,
            "permissions": ["view_story"],
        }
    )
    if pj_membership is None:
        raise ex.InvalidAssignmentError(
            f"{username} is not member or not have permissions"
        )

    user = pj_membership.user

    (
        story_assignment,
        created,
    ) = await story_assignments_repositories.create_story_assignment(
        story=story, user=user
    )
    if created:
        await stories_assignments_events.emit_event_when_story_assignment_is_created(
            story_assignment=story_assignment
        )
        await stories_assignments_notifications.notify_when_story_is_assigned(
            story=story, assigned_to=user, emitted_by=created_by
        )

    return story_assignment


##########################################################
# get story assignment
##########################################################


async def get_story_assignment(
    project_id: UUID, ref: int, username: str
) -> StoryAssignment | None:
    return await story_assignments_repositories.get_story_assignment(
        filters={"project_id": project_id, "ref": ref, "username": username},
        select_related=["story", "user", "project", "workspace"],
    )


##########################################################
# delete story assignment
##########################################################


async def delete_story_assignment(
    story_assignment: StoryAssignment, story: Story, deleted_by: User
) -> bool:
    deleted = await story_assignments_repositories.delete_stories_assignments(
        filters={"id": story_assignment.id}
    )
    if deleted > 0:
        await stories_assignments_events.emit_event_when_story_assignment_is_deleted(
            story_assignment=story_assignment
        )
        await stories_assignments_notifications.notify_when_story_is_unassigned(
            story=story, unassigned_to=story_assignment.user, emitted_by=deleted_by
        )
        return True
    return False
