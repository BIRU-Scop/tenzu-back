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

from django.http import FileResponse, HttpRequest, HttpResponse
from ninja import File, Path, Router, UploadedFile

from attachments import services as attachments_services
from attachments.models import Attachment
from base.api.permissions import check_permissions
from base.utils.files import iterfile
from base.validators import B64UUID
from exceptions import api as ex
from exceptions.api.errors import (
    ERROR_RESPONSE_403,
    ERROR_RESPONSE_404,
    ERROR_RESPONSE_422,
)
from ninja_jwt.authentication import AsyncJWTAuth
from permissions import HasPerm
from stories.attachments import events
from stories.attachments.serializers import StoryAttachmentSerializer
from stories.stories.api import get_story_or_404
from stories.stories.models import Story

attachments_router = Router(auth=AsyncJWTAuth())

# PERMISSIONS
CREATE_STORY_ATTACHMENT = HasPerm("modify_story")
LIST_STORY_ATTACHMENTS = HasPerm("view_story")
DELETE_STORY_ATTACHMENT = HasPerm("modify_story")


################################################
# create story attachment
################################################


@attachments_router.post(
    "/projects/{project_id}/stories/{ref}/attachments",
    url_name="project.story.attachments.create",
    summary="Attach a file to a story",
    response={
        200: StoryAttachmentSerializer,
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def create_story_attachments(
    request,
    project_id: Path[B64UUID],
    ref: int,
    file: UploadedFile = File(...),
) -> Attachment:
    """
    Create an attachment asociate to a story
    """
    story = await get_story_or_404(project_id, ref)
    await check_permissions(
        permissions=CREATE_STORY_ATTACHMENT, user=request.user, obj=story
    )

    event_on_create = partial(
        events.emit_event_when_story_attachment_is_created, project=story.project
    )
    return await attachments_services.create_attachment(
        file=file,
        object=story,
        created_by=request.user,
        event_on_create=event_on_create,
    )


##########################################################
# list story comments
##########################################################


@attachments_router.get(
    "/projects/{project_id}/stories/{ref}/attachments",
    url_name="project.story.attachments.list",
    summary="List story attachments",
    response={
        200: list[StoryAttachmentSerializer],
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def list_story_attachment(
    request: HttpRequest,
    project_id: Path[B64UUID],
    ref: int,
) -> list[Attachment]:
    """
    List the story attachments
    """
    story = await get_story_or_404(project_id=project_id, ref=ref)
    await check_permissions(
        permissions=LIST_STORY_ATTACHMENTS, user=request.user, obj=story
    )
    attachments = await attachments_services.list_attachments(
        content_object=story,
    )
    return attachments


##########################################################
# delete story attachments
##########################################################


@attachments_router.delete(
    "/projects/{project_id}/stories/{ref}/attachments/{attachment_id}",
    url_name="project.story.attachments.delete",
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
    project_id: Path[B64UUID],
    ref: int,
    attachment_id: Path[B64UUID],
) -> tuple[int, None]:
    """
    Delete a story attachment
    """
    story = await get_story_or_404(project_id=project_id, ref=ref)
    attachment = await get_story_attachment_or_404(
        attachment_id=attachment_id, story=story
    )
    await check_permissions(
        permissions=DELETE_STORY_ATTACHMENT, user=request.user, obj=story
    )

    event_on_delete = partial(
        events.emit_event_when_story_attachment_is_deleted, project=story.project
    )
    await attachments_services.delete_attachment(
        attachment=attachment, event_on_delete=event_on_delete
    )
    return 204, None


##########################################################
# download story attachment file
##########################################################


@attachments_router.get(
    "/projects/{project_id}/stories/{ref}/attachments/{attachment_id}",
    auth=None,
    url_name="project.story.attachments.file",
    summary="Download the story attachment file",
    response={
        # FileResponse is not support by django ninja swagger generation
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
    project_id: Path[B64UUID],
    ref: int,
    attachment_id: Path[B64UUID],
    is_view: bool = False,
) -> FileResponse:
    """
    Download a story attachment file
    """
    story = await get_story_or_404(project_id=project_id, ref=ref)
    attachment = await get_story_attachment_or_404(
        attachment_id=attachment_id, story=story
    )
    file = attachment.storaged_object.file

    if is_view:
        response = FileResponse(
            iterfile(file, mode="rb"),
            content_type=attachment.content_type,
        )
    else:
        response = FileResponse(
            iterfile(file, mode="rb"),
            content_type="application/octet-stream; charset=utf-8",
        )
    response.headers["Content-Disposition"] = f"attachment; filename={attachment.name}"
    return response


################################################
# misc:
################################################


async def get_story_attachment_or_404(attachment_id: UUID, story: Story) -> Attachment:
    attachment = await attachments_services.get_attachment(
        id=attachment_id, content_object=story
    )
    if attachment is None:
        raise ex.NotFoundError(f"Attachment {attachment_id} does not exist")

    return attachment
