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

from datetime import datetime
from functools import partial
from typing import TypedDict
from uuid import UUID

from django.core.files import File
from django.core.files.storage import FileSystemStorage
from django.core.files.utils import validate_file_name
from django.db import transaction
from django.db.models.deletion import RestrictedError
from storages.backends.s3 import S3Storage

from commons.storage.models import S3PendingUploadData, StoragedObject, TusUpload
from ninja_jwt.utils import aware_utcnow
from users.models import User

##########################################################
# filters and querysets
##########################################################


class StoragedObjectFilters(TypedDict, total=False):
    id: UUID
    deleted_at__lt: datetime


##########################################################
# create storaged object
##########################################################


async def create_storaged_object(
    file: File,
) -> StoragedObject:
    return await StoragedObject.objects.acreate(file=file)


async def bulk_create_storaged_objects(
    storaged_objects: list[StoragedObject],
) -> list[StoragedObject]:
    return await StoragedObject.objects.abulk_create(storaged_objects)


##########################################################
# list storaged object
##########################################################


def list_storaged_objects(
    filters: StoragedObjectFilters = {},
) -> list[StoragedObject]:
    qs = StoragedObject.objects.all().filter(**filters)
    return list(qs)


##########################################################
# delete storaged object
########################################################


@transaction.atomic
def delete_storaged_object(
    storaged_object: StoragedObject,
) -> bool:
    try:
        with transaction.atomic():
            storaged_object.delete()
    except RestrictedError:
        # This happens when you try to delete a StoragedObject that is being used by someone
        # (using ForeignKey with on_delete=PROTECT).
        # TODO: log this
        return False
    else:
        transaction.on_commit(partial(storaged_object.file.delete, save=False))
        return True


def mark_storaged_object_as_deleted(
    storaged_object: StoragedObject,
) -> None:
    storaged_object.deleted_at = aware_utcnow()
    storaged_object.save(update_fields=["deleted_at"])


##########################################################
# create tus upload
##########################################################


async def create_tus_upload(
    user: User,
    file_name: str,
    file: File | None,
    total_size: int,
    completion_hook: str,
    **completion_hook_parameters,
) -> TusUpload:
    file_field = TusUpload._meta.get_field("file")
    storage = file_field.storage
    s3_pending_upload_data = {}

    if isinstance(storage, S3Storage):
        name = file_field.generate_filename(None, file_name)
        validate_file_name(name, allow_relative_path=True)
        # Potentially find a different name depending on storage constraints.
        name = storage.get_available_name(name, max_length=file_field.max_length)
        # Validate the (potentially) new name.
        validate_file_name(name, allow_relative_path=True)

        name = name[len(storage.location) :].lstrip("/")

        obj = storage.bucket.Object(name)
        multipart_upload = obj.initiate_multipart_upload(
            **storage._get_write_parameters(
                obj.key
            )  # TODO pass contenttype as argument
        )
        # list(storage.bucket.multipart_uploads.filter(UploadIdMarker=multipart_upload.id))
        s3_pending_upload_data = S3PendingUploadData(
            upload_id=multipart_upload.id, parts=[]
        )
    elif isinstance(storage, FileSystemStorage):
        if file is None:
            file = storage.open(file_name, "w")
            file.close()
    else:
        raise ValueError(
            "TusUpload is only supported for S3Storage and FileSystemStorage"
        )
    return await TusUpload.objects.acreate(
        created_by=user,
        file=file,
        total_size=total_size,
        completion_hook=completion_hook,
        completion_hook_parameters=completion_hook_parameters,
        pending_upload_data=s3_pending_upload_data,
    )
