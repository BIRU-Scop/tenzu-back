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

from typing import Any
from uuid import UUID

from base.api import Pagination
from base.db.models import Model
from base.utils.datetime import aware_utcnow
from comments import repositories as comments_repositories
from comments.events import EventOnCreateCallable, EventOnDeleteCallable, EventOnUpdateCallable
from comments.models import Comment
from comments.notifications import NotificationOnCreateCallable
from comments.repositories import CommentFilters, CommentOrderBy
from stories.stories.models import Story
from users.models import User

##########################################################
# create comment
##########################################################


async def create_comment(
    content_object: Model,
    text: str,
    created_by: User,
    event_on_create: EventOnCreateCallable | None = None,
    notification_on_create: NotificationOnCreateCallable | None = None,
) -> Comment:
    comment = await comments_repositories.create_comment(
        content_object=content_object,
        text=text,
        created_by=created_by,
    )

    if event_on_create:
        await event_on_create(comment=comment)
    if notification_on_create:
        await notification_on_create(comment=comment, emitted_by=created_by)

    return comment


##########################################################
# list comments
##########################################################


async def list_paginated_comments(
    content_object: Model,
    offset: int,
    limit: int,
    order_by: CommentOrderBy = [],
) -> tuple[Pagination, int, list[Comment]]:
    filters: CommentFilters = {"content_object": content_object}
    comments = await comments_repositories.list_comments(
        filters=filters,
        select_related=["created_by", "deleted_by"],
        order_by=order_by,
        offset=offset,
        limit=limit,
    )

    total_comments = await comments_repositories.get_total_comments(filters=filters)
    total_not_deleted_comments = await comments_repositories.get_total_comments(
        filters=filters,
        excludes={"deleted": True},
    )
    pagination = Pagination(offset=offset, limit=limit, total=total_comments)

    return pagination, total_not_deleted_comments, comments


##########################################################
# get comment
##########################################################


async def get_comment(id: UUID, content_object: Model) -> Comment | None:
    return await comments_repositories.get_comment(
        filters={"id": id, "content_object": content_object},
        select_related=["created_by", "deleted_by"],
        prefetch_related=["content_object", "project", "workspace"],
    )


##########################################################
# update comment
##########################################################


async def update_comment(
    story: Story,
    comment: Comment,
    values: dict[str, Any] = {},
    event_on_update: EventOnUpdateCallable | None = None,
) -> Comment:
    updated_comment = await comments_repositories.update_comment(comment=comment, values=values)

    if event_on_update:
        await event_on_update(comment=updated_comment)

    return updated_comment


##########################################################
# delete comment
##########################################################


async def delete_comment(
    comment: Comment,
    deleted_by: User,
    event_on_delete: EventOnDeleteCallable | None = None,
) -> Comment:
    updated_comment = await comments_repositories.update_comment(
        comment=comment,
        values={
            "text": "",
            "deleted_by": deleted_by,
            "deleted_at": aware_utcnow(),
        },
    )

    if event_on_delete:
        await event_on_delete(comment=updated_comment)

    return updated_comment
