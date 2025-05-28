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

from ninja import Path, Router

from commons.exceptions import api as ex
from commons.exceptions.api.errors import (
    ERROR_RESPONSE_403,
    ERROR_RESPONSE_404,
    ERROR_RESPONSE_422,
)
from commons.validators import B64UUID
from permissions import check_permissions
from stories.assignments import services as story_assignments_services
from stories.assignments.api.validators import StoryAssignmentValidator
from stories.assignments.models import StoryAssignment
from stories.assignments.serializers import StoryAssignmentSerializer
from stories.stories.api import get_story_or_404
from stories.stories.permissions import StoryPermissionsCheck

assignments_router = Router()


################################################
# assign story (create assignment)
################################################


@assignments_router.post(
    "/projects/{project_id}/stories/{int:ref}/assignments",
    url_name="project.story.assignments.create",
    summary="Create story assignment",
    response={
        200: StoryAssignmentSerializer,
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def create_story_assignment(
    request,
    project_id: Path[B64UUID],
    ref: Path[int],
    form: StoryAssignmentValidator,
) -> StoryAssignment:
    """
    Create a story assignment
    """
    story = await get_story_or_404(project_id, ref)
    await check_permissions(
        permissions=StoryPermissionsCheck.MODIFY.value, user=request.user, obj=story
    )

    return await story_assignments_services.create_story_assignment(
        project_id=project_id,
        story=story,
        user_id=form.user_id,
        created_by=request.user,
    )


################################################
# unassign story (delete assignment)
################################################


@assignments_router.delete(
    "/projects/{project_id}/stories/{int:ref}/assignments/{user_id}",
    url_name="project.story.assignments.delete",
    summary="Delete story assignment",
    response={
        204: None,
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def delete_story_assignment(
    request,
    project_id: Path[B64UUID],
    ref: Path[int],
    user_id: Path[B64UUID],
) -> tuple[int, None]:
    """
    Delete a story assignment
    """
    story_assignment = await get_story_assignment_or_404(project_id, ref, user_id)
    await check_permissions(
        permissions=StoryPermissionsCheck.MODIFY.value,
        user=request.user,
        obj=story_assignment.story,
    )

    await story_assignments_services.delete_story_assignment(
        story_assignment=story_assignment, deleted_by=request.user
    )
    return 204, None


################################################
# misc get story assignment or 404
################################################


async def get_story_assignment_or_404(
    project_id: UUID, ref: int, user_id: UUID
) -> StoryAssignment:
    story_assignment = await story_assignments_services.get_story_assignment(
        project_id=project_id, ref=ref, user_id=user_id
    )
    if story_assignment is None:
        raise ex.NotFoundError(f"User {user_id} is not assigned to story {ref}")

    return story_assignment
