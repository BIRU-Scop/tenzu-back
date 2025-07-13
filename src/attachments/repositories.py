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

from typing import Literal, TypedDict
from uuid import UUID

from django.contrib.contenttypes.models import ContentType
from django.db.models import Model
from ninja import UploadedFile

from attachments.models import Attachment
from base.utils.files import get_size
from commons.storage import repositories as storage_repositories
from users.models import User

##########################################################
# filters and querysets
##########################################################


class AttachmentFilters(TypedDict, total=False):
    id: UUID
    object_content_type: ContentType
    object_id: UUID


AttachmentSelectRelated = list[Literal["storaged_object",] | None]


AttachmentPrefetchRelated = list[
    Literal[
        "content_object",
        "content_object__project",
        "content_object__project__workspace",
    ]
]


##########################################################
# create attachment
##########################################################


async def create_attachment(
    file: UploadedFile,
    created_by: User,
    object: Model,
) -> Attachment:
    storaged_object = await storage_repositories.create_storaged_object(file)

    return await Attachment.objects.acreate(
        storaged_object=storaged_object,
        name=file.name or "unknown",
        size=get_size(file.file),
        content_type=file.content_type or "application/octet-stream",
        content_object=object,
        created_by=created_by,
    )


##########################################################
# list attachments
##########################################################


async def list_attachments(
    filters: AttachmentFilters = {},
    prefetch_related: AttachmentPrefetchRelated = [],
    select_related: AttachmentSelectRelated = ["storaged_object"],
    offset: int | None = None,
    limit: int | None = None,
) -> list[Attachment]:
    qs = (
        Attachment.objects.all()
        .filter(**filters)
        .select_related(*select_related)
        .prefetch_related(*prefetch_related)
    )

    if limit is not None and offset is not None:
        limit += offset

    return [a async for a in qs[offset:limit]]


##########################################################
# get attachment
##########################################################


async def get_attachment(
    filters: AttachmentFilters = {},
    prefetch_related: AttachmentPrefetchRelated = [],
    select_related: AttachmentSelectRelated = ["storaged_object"],
) -> Attachment:
    qs = (
        Attachment.objects.all()
        .filter(**filters)
        .select_related(*select_related)
        .prefetch_related(*prefetch_related)
    )
    return await qs.aget()


##########################################################
# delete attachments
##########################################################


async def delete_attachments(filters: AttachmentFilters) -> int:
    qs = Attachment.objects.all().filter(**filters)
    count, _ = await qs.adelete()
    return count
