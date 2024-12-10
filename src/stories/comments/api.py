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

from functools import partial
from uuid import UUID

from django.http import HttpResponse
from ninja import Path, Query, Router

from base.api import headers as api_headers
from base.api import pagination as api_pagination
from base.api.pagination import PaginationQuery
from base.api.permissions import check_permissions
from base.validators import B64UUID
from comments import services as comments_services
from comments.models import Comment
from comments.serializers import CommentSerializer
from comments.validators import (
    CommentOrderSortQuery,
    CreateCommentValidator,
    UpdateCommentValidator,
)
from exceptions import api as ex
from exceptions.api.errors import (
    ERROR_RESPONSE_403,
    ERROR_RESPONSE_404,
    ERROR_RESPONSE_422,
)
from ninja_jwt.authentication import AsyncJWTAuth
from permissions import HasPerm, IsNotDeleted, IsProjectAdmin, IsRelatedToTheUser
from stories.comments import events, notifications
from stories.stories.api import get_story_or_404
from stories.stories.models import Story

# PERMISSIONS
CREATE_STORY_COMMENT = HasPerm("comment_story")
LIST_STORY_COMMENTS = HasPerm("view_story")
UPDATE_STORY_COMMENT = (
    IsNotDeleted() & IsRelatedToTheUser("created_by") & HasPerm("comment_story")
)
DELETE_STORY_COMMENT = IsNotDeleted() & (
    IsProjectAdmin() | (IsRelatedToTheUser("created_by") & HasPerm("comment_story"))
)

comments_router = Router(auth=AsyncJWTAuth())


##########################################################
# create story comment
##########################################################


@comments_router.post(
    "/projects/{project_id}/stories/{ref}/comments",
    url_name="project.story.comments.create",
    summary="Create story comment",
    response={
        200: CommentSerializer,
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def create_story_comments(
    request,
    project_id: Path[B64UUID],
    ref: int,
    form: CreateCommentValidator,
) -> Comment:
    """
    Add a comment to a story
    """
    story = await get_story_or_404(project_id=project_id, ref=ref)
    await check_permissions(
        permissions=CREATE_STORY_COMMENT, user=request.user, obj=story
    )

    event_on_create = partial(
        events.emit_event_when_story_comment_is_created,
        project=story.project,
    )
    notification_on_create = partial(
        notifications.notify_when_story_comment_is_created,
        story=story,
    )
    return await comments_services.create_comment(
        text=form.text,
        content_object=story,
        created_by=request.user,
        event_on_create=event_on_create,
        notification_on_create=notification_on_create,
    )


##########################################################
# list story comments
##########################################################


@comments_router.get(
    "/projects/{project_id}/stories/{ref}/comments",
    url_name="project.story.comments.list",
    summary="List story comments",
    response={
        200: list[CommentSerializer],
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
# TODO : replace by django ninja paginate
# TODO : check the benefit to have multiple sort ?
# TODO : modify the schema between Query and Service too splited
async def list_story_comments(
    request,
    project_id: Path[B64UUID],
    ref: int,
    response: HttpResponse,
    pagination_params: Query[PaginationQuery],
    order: Query[CommentOrderSortQuery],
) -> list[Comment]:
    """
    List the story comments
    """
    story = await get_story_or_404(project_id=project_id, ref=ref)
    await check_permissions(
        permissions=LIST_STORY_COMMENTS, user=request.user, obj=story
    )
    (
        pagination,
        total_comments,
        comments,
    ) = await comments_services.list_paginated_comments(
        content_object=story,
        offset=pagination_params.offset,
        limit=pagination_params.limit,
        order_by=order.model_dump(),
    )
    api_pagination.set_pagination(response=response, pagination=pagination)
    api_headers.set_headers(
        response=response, headers={"Total-Comments": total_comments}
    )
    return comments


##########################################################
# update story comments
##########################################################


@comments_router.patch(
    "/projects/{project_id}/stories/{ref}/comments/{comment_id}",
    url_name="project.story.comments.update",
    summary="Update story comment",
    response={
        200: CommentSerializer,
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def update_story_comments(
    request,
    project_id: Path[B64UUID],
    ref: int,
    comment_id: Path[B64UUID],
    form: UpdateCommentValidator,
) -> Comment:
    """
    Update a story's comment
    """
    story = await get_story_or_404(project_id=project_id, ref=ref)
    comment = await get_story_comment_or_404(comment_id=comment_id, story=story)
    await check_permissions(
        permissions=UPDATE_STORY_COMMENT, user=request.user, obj=comment
    )

    values = form.dict(exclude_unset=True)
    event_on_update = partial(
        events.emit_event_when_story_comment_is_updated, project=story.project
    )
    return await comments_services.update_comment(
        story=story, comment=comment, values=values, event_on_update=event_on_update
    )


##########################################################
# delete story comments
##########################################################


@comments_router.delete(
    "/projects/{project_id}/stories/{ref}/comments/{comment_id}",
    url_name="project.story.comments.delete",
    summary="Delete story comment",
    response={
        200: CommentSerializer,
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def delete_story_comment(
    request,
    project_id: Path[B64UUID],
    ref: int,
    comment_id: Path[B64UUID],
) -> Comment:
    """
    Delete a comment
    """
    story = await get_story_or_404(project_id=project_id, ref=ref)
    comment = await get_story_comment_or_404(comment_id=comment_id, story=story)
    await check_permissions(
        permissions=DELETE_STORY_COMMENT, user=request.user, obj=comment
    )

    event_on_delete = partial(
        events.emit_event_when_story_comment_is_deleted, project=story.project
    )
    return await comments_services.delete_comment(
        comment=comment, deleted_by=request.user, event_on_delete=event_on_delete
    )


################################################
# misc:
################################################


async def get_story_comment_or_404(comment_id: UUID, story: Story) -> Comment:
    comment = await comments_services.get_comment(id=comment_id, content_object=story)
    if comment is None:
        raise ex.NotFoundError(f"Comment {comment_id} does not exist")

    return comment
