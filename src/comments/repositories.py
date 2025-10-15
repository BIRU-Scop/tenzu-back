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

from typing import Any, Literal, TypedDict
from uuid import UUID

from asgiref.sync import sync_to_async
from django.contrib.contenttypes.models import ContentType
from django.db.models import Model

from comments.models import Comment
from ninja_jwt.utils import aware_utcnow
from users.models import User

##########################################################
# filters and querysets
##########################################################


class CommentFilters(TypedDict, total=False):
    id: UUID
    object_content_type: ContentType
    object_id: UUID
    deleted_by__isnull: bool


CommentSelectRelated = list[
    Literal[
        "created_by",
        "deleted_by",
    ]
    | None
]

CommentPrefetchRelated = list[
    Literal[
        "content_object",
        "content_object__project",
        "content_object__project__workspace",
    ]
]


CommentOrderBy = list[
    Literal[
        "created_at",
        "-created_at",
    ]
]


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
    qs = (
        Comment.objects.all()
        .filter(**filters)
        .select_related(*select_related)
        .order_by(*order_by)
    )

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
) -> Comment:
    qs = (
        Comment.objects.all()
        .filter(**filters)
        .select_related(*select_related)
        .prefetch_related(*prefetch_related)
    )
    return await qs.aget()


##########################################################
# update comment
##########################################################


@sync_to_async
def update_comment(
    comment: Comment, values: dict[str, Any] = {}, update_modified_at=True
) -> Comment:
    for attr, value in values.items():
        setattr(comment, attr, value)

    if update_modified_at:
        comment.modified_at = aware_utcnow()
    comment.save()
    return comment


##########################################################
# delete comment
##########################################################


async def delete_comments(filters: CommentFilters = {}) -> int:
    qs = Comment.objects.all().filter(**filters)
    count, _ = await qs.adelete()
    return count


##########################################################
# misc
##########################################################


async def get_total_comments(filters: CommentFilters = {}) -> int:
    qs = Comment.objects.all().filter(**filters)
    return await qs.acount()
