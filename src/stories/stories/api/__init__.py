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

from uuid import UUID

from django.http import HttpResponse
from ninja import Path, Query, Router

from base.api import Pagination, PaginationQuery, set_pagination
from commons.exceptions import api as ex
from commons.exceptions.api.errors import (
    ERROR_RESPONSE_403,
    ERROR_RESPONSE_404,
    ERROR_RESPONSE_422,
)
from commons.validators import B64UUID
from permissions import check_permissions
from stories.stories import services as stories_services
from stories.stories.api.validators import (
    ReorderStoriesValidator,
    StoryValidator,
    UpdateStoryValidator,
)
from stories.stories.models import Story
from stories.stories.permissions import StoryPermissionsCheck
from stories.stories.serializers import (
    ReorderStoriesSerializer,
    StoryDetailSerializer,
    StorySummarySerializer,
)
from stories.stories.services.exceptions import InvalidStatusError, InvalidStoryRefError
from workflows.api import get_workflow_or_404

stories_router = Router()


################################################
# create story
################################################


@stories_router.post(
    "/projects/{project_id}/workflows/{workflow_slug}/stories",
    url_name="project.stories.create",
    summary="Create a story",
    response={
        200: StoryDetailSerializer,
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def create_story(
    request,
    project_id: Path[B64UUID],
    workflow_slug: str,
    form: StoryValidator,
) -> StoryDetailSerializer:
    """
    Creates a story in the given project workflow
    """
    workflow = await get_workflow_or_404(
        project_id=project_id, workflow_slug=workflow_slug
    )
    await check_permissions(
        permissions=StoryPermissionsCheck.CREATE.value, user=request.user, obj=workflow
    )
    try:
        return await stories_services.create_story(
            title=form.title,
            description=form.description,
            project=workflow.project,
            workflow=workflow,
            status_id=form.status_id,
            user=request.user,
        )
    except InvalidStatusError as e:
        raise ex.BadRequest(str(e))


################################################
# list stories
################################################


@stories_router.get(
    "/projects/{project_id}/workflows/{workflow_slug}/stories",
    url_name="project.stories.list",
    summary="List stories",
    response={
        200: list[StorySummarySerializer],
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
# TODO: pass to django ninja paginate
async def list_stories(
    request,
    project_id: Path[B64UUID],
    workflow_slug: str,
    pagination_params: Query[PaginationQuery],
    response: HttpResponse,
) -> list[StorySummarySerializer]:
    """
    List all the stories for a project workflow
    """
    workflow = await get_workflow_or_404(
        project_id=project_id, workflow_slug=workflow_slug
    )
    await check_permissions(
        permissions=StoryPermissionsCheck.VIEW.value, user=request.user, obj=workflow
    )
    pagination = Pagination(
        offset=pagination_params.offset, limit=pagination_params.limit
    )
    stories = await stories_services.list_stories(
        project_id=project_id,
        workflow_slug=workflow_slug,
        offset=pagination_params.offset,
        limit=pagination_params.limit,
    )

    set_pagination(response=response, pagination=pagination)
    return stories


################################################
# get story
################################################


@stories_router.get(
    "/projects/{project_id}/stories/{ref}",
    url_name="project.stories.get",
    summary="Get story",
    response={
        200: StoryDetailSerializer,
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def get_story(
    request,
    project_id: Path[B64UUID],
    ref: int,
) -> StoryDetailSerializer:
    """
    Get the detailed information of a story.
    """
    story = await get_story_or_404(project_id=project_id, ref=ref)
    await check_permissions(
        permissions=StoryPermissionsCheck.VIEW.value, user=request.user, obj=story
    )

    return await stories_services.get_story_detail(project_id=project_id, ref=ref)


################################################
# update story
################################################


@stories_router.patch(
    "/projects/{project_id}/stories/{ref}",
    url_name="project.stories.update",
    summary="Update story",
    response={
        200: StoryDetailSerializer,
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def update_story(
    request,
    project_id: Path[B64UUID],
    ref: int,
    form: UpdateStoryValidator,
) -> StoryDetailSerializer:
    """
    Update a story from a project.
    """
    story = await get_story_or_404(project_id, ref)
    await check_permissions(
        permissions=StoryPermissionsCheck.MODIFY.value, user=request.user, obj=story
    )

    values = form.model_dump(exclude_unset=True)
    current_version = values.pop("version")
    return await stories_services.update_story(
        story=story,
        updated_by=request.user,
        current_version=current_version,
        values=values,
    )


################################################
# update - reorder stories
################################################


@stories_router.post(
    "/projects/{project_id}/workflows/{workflow_slug}/stories/reorder",
    url_name="project.stories.reorder",
    summary="Reorder stories",
    response={
        200: ReorderStoriesSerializer,
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def reorder_stories(
    request,
    project_id: Path[B64UUID],
    workflow_slug: str,
    form: ReorderStoriesValidator,
) -> ReorderStoriesSerializer:
    """
    Reorder one or more stories; it may change priority and/or status
    """
    workflow = await get_workflow_or_404(
        project_id=project_id, workflow_slug=workflow_slug
    )
    await check_permissions(
        permissions=StoryPermissionsCheck.MODIFY.value, user=request.user, obj=workflow
    )
    try:
        return await stories_services.reorder_stories(
            reordered_by=request.user,
            project=workflow.project,
            workflow=workflow,
            target_status_id=form.status_id,
            stories_refs=form.stories,
            reorder=form.get_reorder_dict(),
        )
    except InvalidStoryRefError as e:
        raise ex.BadRequest(str(e))


################################################
# delete story
################################################


@stories_router.delete(
    "/projects/{project_id}/stories/{ref}",
    url_name="project.stories.delete",
    summary="Delete story",
    response={
        204: None,
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def delete_story(
    request,
    project_id: Path[B64UUID],
    ref: int,
) -> tuple[int, None]:
    """
    Delete a story
    """
    story = await get_story_or_404(project_id=project_id, ref=ref)
    await check_permissions(
        permissions=StoryPermissionsCheck.DELETE.value, user=request.user, obj=story
    )

    await stories_services.delete_story(story=story, deleted_by=request.user)
    return 204, None


################################################
# misc: get story or 404
################################################


async def get_story_or_404(project_id: UUID, ref: int) -> Story:
    story = await stories_services.get_story(project_id=project_id, ref=ref)
    if story is None:
        raise ex.NotFoundError(f"Story {ref} does not exist in the project")

    return story
