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

from ninja import File, Path, Router, UploadedFile

from commons.exceptions.api.errors import (
    ERROR_RESPONSE_403,
    ERROR_RESPONSE_404,
    ERROR_RESPONSE_422,
)
from commons.validators import B64UUID
from mediafiles import services as mediafiles_services
from mediafiles.models import Mediafile
from mediafiles.serializers import MediafileSerializer
from permissions import check_permissions
from stories.stories.api import get_story_or_404
from stories.stories.permissions import StoryPermissionsCheck

mediafiles_router = Router()


################################################
# create mediafile
################################################


# @mediafiles_router.post(
#     "/projects/{project_id}/stories/{int:ref}/mediafiles",
#     url_name="project.story.mediafiles.create",
#     summary="Create mediafiles and attach to a story",
#     response={
#         200: list[MediafileSerializer],
#         403: ERROR_RESPONSE_403,
#         404: ERROR_RESPONSE_404,
#         422: ERROR_RESPONSE_422,
#     },
#     by_alias=True,
# )
# async def create_story_mediafiles(
#     request,
#     project_id: Path[B64UUID],
#     ref: Path[int],
#     files: list[UploadedFile] = File(...),
# ) -> list[Mediafile]:
#     """
#     Add some mediafiles to a story
#     """
#     story = await get_story_or_404(project_id, ref)
#     await check_permissions(
#         permissions=StoryPermissionsCheck.MODIFY.value, user=request.user, obj=story
#     )
#
#     return await mediafiles_services.create_mediafiles(
#         files=files,
#         project=story.project,
#         object=story,
#         created_by=request.user,
#     )
