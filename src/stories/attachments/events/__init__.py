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

from typing import cast

from attachments.models import Attachment
from events import events_manager
from projects.projects.models import Project
from stories.attachments.events.content import (
    CreateStoryAttachmentContent,
    DeleteStoryAttachmentContent,
)
from stories.stories.models import Story

CREATE_STORY_ATTACHMENT = "storiesattachments.create"
DELETE_STORY_ATTACHMENT = "storiesattachments.delete"


async def emit_event_when_story_attachment_is_created(
    attachment: Attachment,
    project: Project,
) -> None:
    story = cast(Story, attachment.content_object)

    await events_manager.publish_on_project_channel(
        project=project,
        type=CREATE_STORY_ATTACHMENT,
        content=CreateStoryAttachmentContent(
            ref=story.ref,
            attachment=attachment,
        ),
    )


async def emit_event_when_story_attachment_is_deleted(
    attachment: Attachment,
    project: Project,
) -> None:
    story = cast(Story, attachment.content_object)

    await events_manager.publish_on_project_channel(
        project=project,
        type=DELETE_STORY_ATTACHMENT,
        content=DeleteStoryAttachmentContent(
            ref=story.ref,
            attachment=attachment,
        ),
    )
