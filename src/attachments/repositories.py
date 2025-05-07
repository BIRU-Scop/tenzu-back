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

from typing import Literal, TypedDict, cast
from uuid import UUID

from django.db.models import Model, QuerySet
from ninja import UploadedFile

from attachments.models import Attachment
from base.db.models import BaseModel, get_contenttype_for_model
from base.utils.files import get_size
from commons.storage import repositories as storage_repositories
from users.models import User

##########################################################
# filters and querysets
##########################################################


DEFAULT_QUERYSET = Attachment.objects.select_related("storaged_object").all()


class AttachmentFilters(TypedDict, total=False):
    id: UUID
    content_object: Model
    content_object__ref: int
    content_object__project_id: UUID


async def _apply_filters_to_queryset(
    qs: QuerySet[Attachment],
    filters: AttachmentFilters = {},
) -> QuerySet[Attachment]:
    filter_data = dict(filters.copy())

    if "content_object" in filters:
        content_object = cast(BaseModel, filter_data.pop("content_object"))
        filter_data["object_content_type"] = await get_contenttype_for_model(
            content_object
        )
        filter_data["object_id"] = content_object.id

    return qs.filter(**filter_data)


AttachmentPrefetchRelated = list[
    Literal[
        "content_object",
        "project",
        "workspace",
    ]
]


async def _apply_prefetch_related_to_queryset(
    qs: QuerySet[Attachment],
    prefetch_related: AttachmentPrefetchRelated,
) -> QuerySet[Attachment]:
    prefetch_related_data = []

    for key in prefetch_related:
        if key == "workspace":
            prefetch_related_data.append("content_object__project__workspace")
        elif key == "project":
            prefetch_related_data.append("content_object__project")
        else:
            prefetch_related_data.append(key)

    return qs.prefetch_related(*prefetch_related_data)


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
    offset: int | None = None,
    limit: int | None = None,
) -> list[Attachment]:
    qs = await _apply_filters_to_queryset(qs=DEFAULT_QUERYSET, filters=filters)
    qs = await _apply_prefetch_related_to_queryset(
        qs=qs, prefetch_related=prefetch_related
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
) -> Attachment:
    qs = await _apply_filters_to_queryset(qs=DEFAULT_QUERYSET, filters=filters)
    qs = await _apply_prefetch_related_to_queryset(
        qs=qs, prefetch_related=prefetch_related
    )
    return await qs.aget()


##########################################################
# delete attachments
##########################################################


async def delete_attachments(filters: AttachmentFilters) -> int:
    qs = await _apply_filters_to_queryset(qs=DEFAULT_QUERYSET, filters=filters)
    count, _ = await qs.adelete()
    return count
