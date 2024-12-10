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

from comments.models import Comment
from notifications import services as notifications_services
from stories.comments.notifications.content import StoryCommentCreateNotificationContent
from stories.stories.models import Story
from users.models import User

STORY_COMMENT_CREATE = "story_comment.create"


async def notify_when_story_comment_is_created(
    story: Story, comment: Comment, emitted_by: User
) -> None:
    notified_users = {u async for u in story.assignees.all()}
    if story.created_by:
        notified_users.add(story.created_by)
    notified_users.discard(emitted_by)

    await notifications_services.notify_users(
        type=STORY_COMMENT_CREATE,
        emitted_by=emitted_by,
        notified_users=notified_users,
        content=StoryCommentCreateNotificationContent(
            project=story.project,
            story=story,
            commented_by=emitted_by,
            comment=comment,
        ),
    )
