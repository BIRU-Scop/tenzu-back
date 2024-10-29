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
from stories.stories.models import Story
from stories.stories.notifications.content import (
    StoryDeleteNotificationContent,
    StoryStatusChangeNotificationContent,
    StoryWorkflowChangeNotificationContent,
)
from users.models import User

STORIES_STATUS_CHANGE = "stories.status_change"
STORIES_WORKFLOW_CHANGE = "stories.workflow_change"
STORIES_DELETE = "stories.delete"


async def notify_when_story_status_change(story: Story, status: str, emitted_by: User) -> None:
    """
    Emit notification when a story status changes
    """
    notified_users = {u async for u in story.assignees.all()}
    if story.created_by:
        notified_users.add(story.created_by)
    notified_users.discard(emitted_by)

    await notifications_services.notify_users(
        type=STORIES_STATUS_CHANGE,
        emitted_by=emitted_by,
        notified_users=notified_users,
        content=StoryStatusChangeNotificationContent(
            project=story.project,
            story=story,
            changed_by=emitted_by,
            status=status,
        ),
    )


async def notify_when_story_workflow_change(story: Story, workflow: str, status: str, emitted_by: User) -> None:
    """
    Emit notification when a story workflow changes
    """
    notified_users = {u async for u in story.assignees.all()}
    if story.created_by:
        notified_users.add(story.created_by)
    notified_users.discard(emitted_by)

    await notifications_services.notify_users(
        type=STORIES_WORKFLOW_CHANGE,
        emitted_by=emitted_by,
        notified_users=notified_users,
        content=StoryWorkflowChangeNotificationContent(
            project=story.project,
            story=story,
            changed_by=emitted_by,
            workflow=workflow,
            status=status,
        ),
    )


async def notify_when_story_is_deleted(story: Story, emitted_by: User) -> None:
    """
    Emit notification when a story is deleted
    """
    notified_users = set()
    if story.created_by:
        notified_users.add(story.created_by)
    notified_users.discard(emitted_by)

    await notifications_services.notify_users(
        type=STORIES_DELETE,
        emitted_by=emitted_by,
        notified_users=notified_users,
        content=StoryDeleteNotificationContent(
            project=story.project,
            story=story,
            deleted_by=emitted_by,
        ),
    )
