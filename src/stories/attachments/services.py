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

from ninja import UploadedFile

from attachments import services as attachments_services
from attachments.models import Attachment
from projects.projects.models import Project
from stories.attachments import events
from stories.stories.models import Story
from users.models import User


async def create_attachment(
    file: UploadedFile,
    created_by: User,
    story: Story,
) -> Attachment:
    event_on_create = partial(
        events.emit_event_when_story_attachment_is_created, project=story.project
    )
    return await attachments_services.create_attachment(
        file=file,
        object=story,
        created_by=created_by,
        event_on_create=event_on_create,
    )


async def delete_attachment(attachment: Attachment, project: Project):
    event_on_delete = partial(
        events.emit_event_when_story_attachment_is_deleted, project=project
    )
    await attachments_services.delete_attachment(
        attachment=attachment, event_on_delete=event_on_delete
    )
