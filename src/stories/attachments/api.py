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

from django.conf import settings
from django.http import FileResponse, HttpRequest
from ninja import File, Path, Router, UploadedFile

from attachments import services as attachments_services
from attachments.models import Attachment
from base.serializers import BaseDataModel
from base.utils.files import iterfile
from commons.exceptions import api as ex
from commons.exceptions.api.errors import (
    ERROR_RESPONSE_403,
    ERROR_RESPONSE_404,
    ERROR_RESPONSE_422,
)
from commons.validators import B64UUID
from permissions import check_permissions
from stories.attachments import services as services
from stories.attachments.serializers import StoryAttachmentSerializer
from stories.stories.api import get_story_or_404
from stories.stories.models import Story
from stories.stories.permissions import StoryPermissionsCheck

attachments_router = Router()


################################################
# create story attachment
################################################


@attachments_router.post(
    "/projects/{project_id}/stories/{int:ref}/attachments",
    url_name="project.story.attachments.create",
    summary="Attach a file to a story",
    response={
        200: BaseDataModel[StoryAttachmentSerializer],
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def create_story_attachments(
    request,
    project_id: Path[B64UUID],
    ref: Path[int],
    file: File[(UploadedFile, {"max_length": settings.MAX_UPLOAD_FILE_SIZE})],
) -> Attachment:
    """
    Create an attachment associated to a story
    """
    story = await get_story_or_404(project_id, ref)
    await check_permissions(
        permissions=StoryPermissionsCheck.MODIFY.value, user=request.user, obj=story
    )

    return await services.create_attachment(
        file=file,
        story=story,
        created_by=request.user,
    )


##########################################################
# list story attachments
##########################################################


@attachments_router.get(
    "/projects/{project_id}/stories/{int:ref}/attachments",
    url_name="project.story.attachments.list",
    summary="List story attachments",
    response={
        200: BaseDataModel[list[StoryAttachmentSerializer]],
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def list_story_attachment(
    request: HttpRequest,
    project_id: Path[B64UUID],
    ref: Path[int],
) -> list[Attachment]:
    """
    List the story attachments
    """
    story = await get_story_or_404(project_id=project_id, ref=ref)
    await check_permissions(
        permissions=StoryPermissionsCheck.VIEW.value, user=request.user, obj=story
    )
    attachments = await attachments_services.list_attachments(
        content_object=story,
    )
    return attachments


##########################################################
# delete story attachments
##########################################################


@attachments_router.delete(
    "/stories/attachments/{attachment_id}",
    url_name="story.attachments.delete",
    summary="Delete story attachment",
    response={
        204: None,
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def delete_story_attachment(
    request,
    attachment_id: Path[B64UUID],
) -> tuple[int, None]:
    """
    Delete a story attachment
    """
    attachment = await get_story_attachment_or_404(attachment_id=attachment_id)
    await check_permissions(
        permissions=StoryPermissionsCheck.MODIFY.value,
        user=request.user,
        obj=attachment.content_object,
    )

    await services.delete_attachment(
        attachment=attachment, project=attachment.content_object.project
    )
    return 204, None


##########################################################
# download story attachment file
##########################################################


@attachments_router.get(
    "/stories/attachments/{attachment_id}",
    url_name="story.attachments.file",
    summary="Download the story attachment file",
    response={
        # FileResponse is not supported by django ninja swagger generation
        # As presented in the documentation, type the result as str
        # https://django-ninja.dev/guides/response/#filefield-and-imagefield
        200: str,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def get_story_attachment_file(
    request,
    attachment_id: Path[B64UUID],
    is_view: bool = False,
) -> FileResponse:
    """
    Download a story attachment file
    """
    attachment = await get_story_attachment_or_404(attachment_id=attachment_id)
    await check_permissions(
        permissions=StoryPermissionsCheck.VIEW.value,
        user=request.user,
        obj=attachment.content_object,
    )

    file = attachment.storaged_object.file

    response = FileResponse(
        iterfile(file, mode="rb"),
        content_type=attachment.content_type,
        as_attachment=not is_view,
        filename=attachment.name,
    )
    return response


################################################
# misc:
################################################


async def get_story_attachment_or_404(
    attachment_id: UUID,
) -> Attachment:
    try:
        attachment = await attachments_services.get_attachment(
            attachment_id=attachment_id
        )
    except Attachment.DoesNotExist as e:
        raise ex.NotFoundError(f"Attachment {attachment_id} does not exist") from e
    if not isinstance(attachment.content_object, Story):
        raise ex.NotFoundError(f"Attachment {attachment_id} is not a story attachment")

    return attachment
