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

from django.http import HttpResponse
from ninja import Path, Query, Router

from base.api import pagination as api_pagination
from base.api.pagination import PaginationQuery
from base.serializers import BaseDataModel
from comments import services as comments_services
from comments.models import Comment
from comments.serializers import CommentSerializer
from comments.validators import (
    CommentOrderSortQuery,
    CreateCommentValidator,
    UpdateCommentValidator,
)
from commons.exceptions import api as ex
from commons.exceptions.api.errors import (
    ERROR_RESPONSE_403,
    ERROR_RESPONSE_404,
    ERROR_RESPONSE_422,
)
from commons.validators import B64UUID
from permissions import (
    check_permissions,
)
from stories.comments import services as services
from stories.comments.permissions import CommentPermissionsCheck
from stories.stories.api import get_story_or_404
from stories.stories.models import Story

comments_router = Router()


##########################################################
# create story comment
##########################################################


@comments_router.post(
    "/projects/{project_id}/stories/{int:ref}/comments",
    url_name="project.story.comments.create",
    summary="Create story comment",
    response={
        200: BaseDataModel[CommentSerializer],
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def create_story_comments(
    request,
    project_id: Path[B64UUID],
    ref: Path[int],
    form: CreateCommentValidator,
) -> Comment:
    """
    Add a comment to a story
    """
    story = await get_story_or_404(project_id=project_id, ref=ref, get_assignees=True)
    await check_permissions(
        permissions=CommentPermissionsCheck.CREATE.value, user=request.user, obj=story
    )
    return await services.create_comment(
        comment_text=form.text,
        created_by=request.user,
        story=story,
    )


##########################################################
# list story comments
##########################################################


@comments_router.get(
    "/projects/{project_id}/stories/{int:ref}/comments",
    url_name="project.story.comments.list",
    summary="List story comments",
    response={
        200: BaseDataModel[list[CommentSerializer]],
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
# TODO : replace by django ninja paginate
# TODO : check the benefit to have multiple sort ?
# TODO : modify the schema between Query and Service too split
async def list_story_comments(
    request,
    project_id: Path[B64UUID],
    ref: Path[int],
    response: HttpResponse,
    pagination_params: Query[PaginationQuery],
    order: Query[CommentOrderSortQuery],
) -> list[Comment]:
    """
    List the story comments
    """
    story = await get_story_or_404(project_id=project_id, ref=ref)
    await check_permissions(
        permissions=CommentPermissionsCheck.VIEW.value, user=request.user, obj=story
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
    response.headers["Tenzu-Total-Comments"] = total_comments
    return comments


##########################################################
# update story comments
##########################################################


@comments_router.patch(
    "/stories/comments/{comment_id}",
    url_name="story.comments.update",
    summary="Update story comment",
    response={
        200: BaseDataModel[CommentSerializer],
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def update_story_comments(
    request,
    comment_id: Path[B64UUID],
    form: UpdateCommentValidator,
) -> Comment:
    """
    Update a story's comment
    """
    comment = await get_story_comment_or_404(comment_id=comment_id)
    await check_permissions(
        permissions=CommentPermissionsCheck.MODIFY.value, user=request.user, obj=comment
    )

    values = form.dict(exclude_unset=True)
    return await services.update_comment(
        comment=comment, project=comment.content_object.project, values=values
    )


##########################################################
# delete story comments
##########################################################


@comments_router.delete(
    "/stories/comments/{comment_id}",
    url_name="story.comments.delete",
    summary="Delete story comment",
    response={
        200: BaseDataModel[CommentSerializer],
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def delete_story_comment(
    request,
    comment_id: Path[B64UUID],
) -> Comment:
    """
    Delete a comment
    """
    comment = await get_story_comment_or_404(comment_id=comment_id)
    await check_permissions(
        permissions=CommentPermissionsCheck.DELETE.value, user=request.user, obj=comment
    )

    return await services.delete_comment(
        comment=comment, deleted_by=request.user, project=comment.content_object.project
    )


################################################
# misc:
################################################


async def get_story_comment_or_404(
    comment_id: UUID,
) -> Comment:
    try:
        comment = await comments_services.get_comment(comment_id=comment_id)
    except Comment.DoesNotExist as e:
        raise ex.NotFoundError(f"Comment {comment_id} does not exist") from e
    if not isinstance(comment.content_object, Story):
        raise ex.NotFoundError(f"Comment {comment_id} is not a story comment")

    return comment
