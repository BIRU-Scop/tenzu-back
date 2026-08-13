# -*- coding: utf-8 -*-
# Copyright (C) 2024-2026 BIRU
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
from base64 import urlsafe_b64decode
from datetime import datetime
from uuid import UUID

from django.http import HttpRequest
from ninja import UploadedFile

from commons.storage import repositories as storage_repositories
from commons.storage.models import TusUpload
from users.models import User

##########################################################
# storaged objects
##########################################################


def clean_deleted_storaged_objects(before: datetime) -> int:
    storaged_objects = storage_repositories.list_storaged_objects(
        filters={"deleted_at__lt": before}
    )
    deleted = 0
    for storaged_object in storaged_objects:
        if storage_repositories.delete_storaged_object(storaged_object=storaged_object):
            deleted += 1

    return deleted


##########################################################
# tus upload
##########################################################


async def create_tus_upload(
    user: User,
    file_name: str,
    file_content_type: str,
    request: HttpRequest,
    content_size: int,
    total_size: int,
    completion_hook: str,
    completion_hook_parameters: dict,
) -> TusUpload:
    request.content_type = file_content_type
    return await storage_repositories.create_tus_upload(
        user,
        file_name,
        request,
        content_size,
        total_size,
        completion_hook,
        completion_hook_parameters,
    )


async def process_new_tus_content(
    tus_upload: TusUpload,
    request: HttpRequest,
    content_size: int,
) -> TusUpload:
    return await storage_repositories.process_new_tus_content(
        tus_upload=tus_upload,
        request=request,
        content_size=content_size,
    )


def parse_tus_metadata(upload_metadata: str) -> dict:
    if not upload_metadata:
        return {}
    return {
        key: urlsafe_b64decode(value[0]).decode(encoding="utf-8") if value else None
        for key, *value in (data.split(" ") for data in upload_metadata.split(","))
    }


async def get_tus_upload(tus_upload_id: UUID) -> TusUpload:
    return await storage_repositories.get_tus_upload(tus_upload_id=tus_upload_id)


def clean_expired_tus_uploads(before: datetime) -> int:
    tus_uploads = storage_repositories.list_tus_uploads(
        filters={"created_at__lt": before}
    )
    deleted = 0
    for tus_upload in tus_uploads:
        if storage_repositories.delete_tus_upload(tus_upload=tus_upload):
            deleted += 1

    return deleted
