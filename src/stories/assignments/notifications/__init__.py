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

from notifications import services as notifications_services
from stories.assignments.notifications.content import (
    StoryAssignNotificationContent,
    StoryUnassignNotificationContent,
)
from stories.stories.models import Story
from users.models import User

STORIES_ASSIGN = "stories.assign"
STORIES_UNASSIGN = "stories.unassign"


async def notify_when_story_is_assigned(
    story: Story, assigned_to: User, emitted_by: User
) -> None:
    """
    Emit notification when a story is assigned.
    """
    notified_users = {assigned_to}
    if story.created_by:
        notified_users.add(story.created_by)
    notified_users.discard(emitted_by)

    await notifications_services.notify_users(
        type=STORIES_ASSIGN,
        emitted_by=emitted_by,
        notified_users=notified_users,
        content=StoryAssignNotificationContent(
            project=story.project,
            story=story,
            assigned_by=emitted_by,
            assigned_to=assigned_to,
        ),
    )


async def notify_when_story_is_unassigned(
    story: Story, unassigned_to: User, emitted_by: User
) -> None:
    """
    Emit notification when story is unassigned.
    """
    notified_users = {unassigned_to}
    if story.created_by:
        notified_users.add(story.created_by)
    notified_users.discard(emitted_by)

    await notifications_services.notify_users(
        type=STORIES_UNASSIGN,
        emitted_by=emitted_by,
        notified_users=notified_users,
        content=StoryUnassignNotificationContent(
            project=story.project,
            story=story,
            unassigned_by=emitted_by,
            unassigned_to=unassigned_to,
        ),
    )
