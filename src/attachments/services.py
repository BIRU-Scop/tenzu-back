# -*- coding: utf-8 -*-
# Copyright (C) 2024-2025 BIRU
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

from django.db.models import Model
from ninja import UploadedFile

from attachments import repositories as attachments_repositories
from attachments.events import EventOnCreateCallable, EventOnDeleteCallable
from attachments.models import Attachment
from base.db.models import get_contenttype_for_model
from users.models import User

##########################################################
# create attachment
##########################################################


async def create_attachment(
    file: UploadedFile,
    created_by: User,
    object: Model,
    event_on_create: EventOnCreateCallable | None = None,
) -> Attachment:
    attachment = await attachments_repositories.create_attachment(
        file=file,
        object=object,
        created_by=created_by,
    )

    if event_on_create:
        await event_on_create(attachment=attachment)

    return attachment


##########################################################
# list attachments
##########################################################


async def list_attachments(
    content_object: Model,
) -> list[Attachment]:
    return await attachments_repositories.list_attachments(
        filters={
            "object_content_type": await get_contenttype_for_model(content_object),
            "object_id": content_object.id,
        },
        prefetch_related=["content_object", "content_object__project"],
    )


##########################################################
# get attachment
##########################################################


async def get_attachment(
    attachment_id: UUID,
) -> Attachment:
    return await attachments_repositories.get_attachment(
        filters={"id": attachment_id},
        prefetch_related=["content_object", "content_object__project"],
    )


##########################################################
# delete comment
##########################################################


async def delete_attachment(
    attachment: Attachment,
    event_on_delete: EventOnDeleteCallable | None = None,
) -> bool:
    was_deleted = await attachments_repositories.delete_attachments(
        filters={"id": attachment.id},
    )

    if was_deleted and event_on_delete:
        await event_on_delete(attachment=attachment)

    return bool(was_deleted)
