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

from typing import Any, Literal, TypedDict, cast
from uuid import UUID

from asgiref.sync import sync_to_async
from django.db.models import Model, QuerySet

from base.db.models import BaseModel, get_contenttype_for_model
from comments.models import Comment
from ninja_jwt.utils import aware_utcnow
from users.models import User

##########################################################
# filters and querysets
##########################################################


DEFAULT_QUERYSET = Comment.objects.all()


class CommentFilters(TypedDict, total=False):
    id: UUID
    content_object: Model


async def _apply_filters_to_queryset(
    qs: QuerySet[Comment],
    filters: CommentFilters = {},
) -> QuerySet[Comment]:
    filter_data = dict(filters.copy())

    if "content_object" in filters:
        content_object = cast(BaseModel, filter_data.pop("content_object"))
        filter_data["object_content_type"] = await get_contenttype_for_model(
            content_object
        )
        filter_data["object_id"] = content_object.id

    return qs.filter(**filter_data)


class CommentExcludes(TypedDict, total=False):
    deleted: bool


async def _apply_excludes_to_queryset(
    qs: QuerySet[Comment],
    excludes: CommentExcludes = {},
) -> QuerySet[Comment]:
    excludes_data = dict(excludes.copy())

    if "deleted" in excludes_data and excludes_data.pop("deleted"):
        excludes_data["deleted_by__isnull"] = False

    return qs.exclude(**excludes_data)


CommentSelectRelated = list[
    Literal[
        "created_by",
        "deleted_by",
    ]
    | None
]


async def _apply_select_related_to_queryset(
    qs: QuerySet[Comment],
    select_related: CommentSelectRelated = [None],
) -> QuerySet[Comment]:
    return qs.select_related(*select_related)


CommentPrefetchRelated = list[
    Literal[
        "content_object",
        "project",
        "workspace",
    ]
]


async def _apply_prefetch_related_to_queryset(
    qs: QuerySet[Comment],
    prefetch_related: CommentPrefetchRelated,
) -> QuerySet[Comment]:
    prefetch_related_data = []

    for key in prefetch_related:
        if key == "workspace":
            prefetch_related_data.append("content_object__project__workspace")
        elif key == "project":
            prefetch_related_data.append("content_object__project")
        else:
            prefetch_related_data.append(key)

    return qs.prefetch_related(*prefetch_related_data)


CommentOrderBy = list[
    Literal[
        "created_at",
        "-created_at",
    ]
]


async def _apply_order_by_to_queryset(
    qs: QuerySet[Comment],
    order_by: CommentOrderBy,
) -> QuerySet[Comment]:
    return qs.order_by(*order_by)


##########################################################
# create comment
##########################################################


async def create_comment(
    content_object: Model,
    text: str,
    created_by: User,
) -> Comment:
    return await Comment.objects.acreate(
        text=text,
        created_by=created_by,
        content_object=content_object,
    )


##########################################################
# list comments
##########################################################


async def list_comments(
    filters: CommentFilters = {},
    select_related: CommentSelectRelated = [None],
    order_by: CommentOrderBy = ["-created_at"],
    offset: int | None = None,
    limit: int | None = None,
) -> list[Comment]:
    qs = await _apply_filters_to_queryset(qs=DEFAULT_QUERYSET, filters=filters)
    qs = await _apply_select_related_to_queryset(qs=qs, select_related=select_related)
    qs = await _apply_order_by_to_queryset(order_by=order_by, qs=qs)

    if limit is not None and offset is not None:
        limit += offset

    return [c async for c in qs[offset:limit]]


##########################################################
# get comment
##########################################################


async def get_comment(
    filters: CommentFilters = {},
    select_related: CommentSelectRelated = [None],
    prefetch_related: CommentPrefetchRelated = [],
    excludes: CommentExcludes = {},
) -> Comment:
    qs = await _apply_filters_to_queryset(qs=DEFAULT_QUERYSET, filters=filters)
    qs = await _apply_excludes_to_queryset(qs=qs, excludes=excludes)
    qs = await _apply_select_related_to_queryset(qs=qs, select_related=select_related)
    qs = await _apply_prefetch_related_to_queryset(
        qs=qs, prefetch_related=prefetch_related
    )
    return await qs.aget()


##########################################################
# update comment
##########################################################


@sync_to_async
def update_comment(comment: Comment, values: dict[str, Any] = {}) -> Comment:
    for attr, value in values.items():
        setattr(comment, attr, value)

    comment.modified_at = aware_utcnow()
    comment.save()
    return comment


##########################################################
# delete comment
##########################################################


async def delete_comments(filters: CommentFilters = {}) -> int:
    qs = await _apply_filters_to_queryset(qs=DEFAULT_QUERYSET, filters=filters)
    count, _ = await qs.adelete()
    return count


##########################################################
# misc
##########################################################


async def get_total_comments(
    filters: CommentFilters = {}, excludes: CommentExcludes = {}
) -> int:
    qs = await _apply_filters_to_queryset(qs=DEFAULT_QUERYSET, filters=filters)
    qs = await _apply_excludes_to_queryset(qs=qs, excludes=excludes)
    return await qs.acount()
