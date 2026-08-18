# -*- coding: utf-8 -*-
# Copyright (C) 2026 BIRU
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

from ninja import Path, Router, Status

from base.serializers import BaseDataSchema
from commons.exceptions import api as ex
from commons.exceptions.api.errors import (
    ERROR_RESPONSE_400,
    ERROR_RESPONSE_403,
    ERROR_RESPONSE_404,
    ERROR_RESPONSE_422,
)
from commons.validators import B64UUID
from permissions import check_permissions
from projects.projects.api import get_project_or_404
from stories.stories.api import get_story_or_404
from stories.stories.permissions import StoryPermissionsCheck
from stories.tags import repositories as story_tags_repositories
from stories.tags import services as story_tags_services
from stories.tags.api.validators import (
    StoryTagAssignValidator,
    StoryTagCreateValidator,
    StoryTagUpdateValidator,
)
from stories.tags.models import StoryTag, StoryTagAssignment, StoryTagWithCount
from stories.tags.permissions import StoryTagPermissionsCheck
from stories.tags.serializers import (
    StoryTagAssignmentSerializer,
    StoryTagWithCountSerializer,
)

story_tags_router = Router()


################################################
# create story tag
################################################


@story_tags_router.post(
    "/projects/{project_id}/stories/tags",
    url_name="project.storytag.create",
    summary="Create story tag",
    response={
        200: BaseDataSchema[StoryTagWithCountSerializer],
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def create_story_tag(
    request,
    project_id: Path[B64UUID],
    form: StoryTagCreateValidator,
) -> StoryTag:
    """
    Create a story tag in a project
    """
    project = await get_project_or_404(project_id)
    await check_permissions(
        permissions=StoryTagPermissionsCheck.CREATE.value,
        user=request.user,
        obj=project,
    )

    return await story_tags_services.create_story_tag(
        project=project, label=form.label, color=form.color
    )


################################################
# list story tags
################################################


@story_tags_router.get(
    "/projects/{project_id}/stories/tags",
    url_name="project.storytag.list",
    summary="List project story tags",
    response={
        200: BaseDataSchema[list[StoryTagWithCountSerializer]],
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def list_story_tags(
    request,
    project_id: Path[B64UUID],
) -> list[StoryTag]:
    """
    List the story tags of a project with their usage count
    """
    project = await get_project_or_404(project_id)
    await check_permissions(
        permissions=StoryTagPermissionsCheck.VIEW.value,
        user=request.user,
        obj=project,
    )

    return await story_tags_services.list_story_tags(project_id=project_id)


################################################
# update story tag
################################################


@story_tags_router.patch(
    "/stories/tags/{tag_id}",
    url_name="project.storytag.update",
    summary="Update story tag",
    response={
        200: BaseDataSchema[StoryTagWithCountSerializer],
        400: ERROR_RESPONSE_400,
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def update_story_tag(
    request,
    tag_id: Path[B64UUID],
    form: StoryTagUpdateValidator,
) -> StoryTag:
    """
    Update a story tag
    """
    story_tag = await get_story_tag_or_404(story_tag_id=tag_id)
    await check_permissions(
        permissions=StoryTagPermissionsCheck.MODIFY.value,
        user=request.user,
        obj=story_tag.project,
    )

    values = form.model_dump()
    return await story_tags_services.update_story_tag(
        story_tag=story_tag, values=values
    )


################################################
# delete story tag
################################################


@story_tags_router.delete(
    "/stories/tags/{tag_id}",
    url_name="project.storytag.delete",
    summary="Delete story tag",
    response={
        204: None,
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def delete_story_tag(
    request,
    tag_id: Path[B64UUID],
) -> Status[None]:
    """
    Delete a story tag; it is automatically removed from all the stories carrying it
    """
    story_tag = await get_story_tag_or_404(story_tag_id=tag_id)
    await check_permissions(
        permissions=StoryTagPermissionsCheck.DELETE.value,
        user=request.user,
        obj=story_tag.project,
    )

    await story_tags_services.delete_story_tag(story_tag=story_tag)
    return Status(204, None)


################################################
# assign story tag (create story tag assignment)
################################################


@story_tags_router.post(
    "/projects/{project_id}/stories/{int:ref}/tags",
    url_name="project.story.tags.create",
    summary="Assign a tag to a story (create story tag assignment)",
    response={
        200: BaseDataSchema[StoryTagAssignmentSerializer],
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def create_story_tag_assignment(
    request,
    project_id: Path[B64UUID],
    ref: Path[int],
    form: StoryTagAssignValidator,
) -> StoryTagAssignment:
    """
    Assign a tag of the project to a story; assigning an already-assigned tag is
    an idempotent no-op
    """
    story = await get_story_or_404(project_id, ref)
    await check_permissions(
        permissions=StoryPermissionsCheck.MODIFY.value, user=request.user, obj=story
    )
    story_tag = await get_story_tag_or_404(story_tag_id=form.tag_id)

    return await story_tags_services.create_story_tag_assignment(
        story=story, tag=story_tag
    )


################################################
# unassign story tag (delete story tag assignment)
################################################


@story_tags_router.delete(
    "/projects/{project_id}/stories/{int:ref}/tags/{tag_id}",
    url_name="project.story.tags.delete",
    summary="Unassign a tag from a story (delete story tag assignment)",
    response={
        204: None,
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def delete_story_tag_assignment(
    request,
    project_id: Path[B64UUID],
    ref: Path[int],
    tag_id: Path[B64UUID],
) -> Status[None]:
    """
    Unassign a tag from a story
    """
    story = await get_story_or_404(project_id, ref)
    await check_permissions(
        permissions=StoryPermissionsCheck.MODIFY.value, user=request.user, obj=story
    )
    story_tag_assignment = await get_story_tag_assignment_or_404(
        story_id=story.id, tag_id=tag_id
    )

    await story_tags_services.delete_story_tag_assignment(
        story_tag_assignment=story_tag_assignment
    )
    return Status(204, None)


################################################
# misc
################################################


async def get_story_tag_or_404(story_tag_id: UUID) -> StoryTagWithCount:
    try:
        return await story_tags_repositories.get_story_tag(story_tag_id=story_tag_id)
    except StoryTag.DoesNotExist as e:
        raise ex.NotFoundError("Story tag does not exist") from e


async def get_story_tag_assignment_or_404(
    story_id: UUID, tag_id: UUID
) -> StoryTagAssignment:
    try:
        return await story_tags_repositories.get_story_tag_assignment(
            story_id=story_id, tag_id=tag_id
        )
    except StoryTagAssignment.DoesNotExist as e:
        raise ex.NotFoundError("Story tag assignment does not exist") from e
