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

from functools import partial
from typing import Any

from comments import services as comments_services
from comments.models import Comment
from projects.projects.models import Project
from stories.comments import events, notifications
from stories.stories.models import Story
from users.models import User


async def create_comment(
    comment_text: str,
    created_by: User,
    story: Story,
) -> Comment:
    event_on_create = partial(
        events.emit_event_when_story_comment_is_created,
        project=story.project,
    )
    notification_on_create = partial(
        notifications.notify_when_story_comment_is_created,
        story=story,
    )
    return await comments_services.create_comment(
        text=comment_text,
        content_object=story,
        created_by=created_by,
        event_on_create=event_on_create,
        notification_on_create=notification_on_create,
    )


async def update_comment(
    comment: Comment, project: Project, values: dict[str, Any]
) -> Comment:
    event_on_update = partial(
        events.emit_event_when_story_comment_is_updated, project=project
    )
    return await comments_services.update_comment(
        comment=comment, values=values, event_on_update=event_on_update
    )


async def delete_comment(comment: Comment, deleted_by: User, project: Project):
    event_on_delete = partial(
        events.emit_event_when_story_comment_is_deleted, project=project
    )
    return await comments_services.delete_comment(
        comment=comment, deleted_by=deleted_by, event_on_delete=event_on_delete
    )
