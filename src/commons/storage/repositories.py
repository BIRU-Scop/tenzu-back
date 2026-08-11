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

from asgiref.sync import iscoroutinefunction, sync_to_async
from django.core.files import File
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage, Storage
from django.core.files.utils import validate_file_name
from django.db import transaction
from django.db.models.deletion import RestrictedError
from django.http import HttpRequest
from django.http.multipartparser import ChunkIter, LazyStream, MultiPartParser
from django.utils.module_loading import import_string
from s3transfer.utils import ChunksizeAdjuster
from storages.backends.s3 import S3Storage

from commons.exceptions import api as api_ex
from commons.storage.models import (
    S3Part,
    S3PendingUploadData,
    StoragedObject,
    TusUpload,
)
from commons.utils import transaction_atomic_async, transaction_on_commit_async
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
    request: HttpRequest,
    content_size: int,
    total_size: int,
    completion_hook: str,
    completion_hook_parameters: dict,
) -> TusUpload:
    file_field = TusUpload._meta.get_field("file")
    storage = file_field.storage
    s3_pending_upload_data = {}
    file_name = MultiPartParser.sanitize_file_name(None, file_name)
    file = None

    if isinstance(storage, S3Storage):
        name = file_field.generate_filename(None, file_name)
        validate_file_name(name, allow_relative_path=True)
        # Potentially find a different name depending on storage constraints.
        name = storage.get_available_name(name, max_length=file_field.max_length)
        # Validate the (potentially) new name.
        validate_file_name(name, allow_relative_path=True)

        obj = storage._open(name, "w+b").obj

        multipart_upload = obj.initiate_multipart_upload(
            **storage._get_write_parameters(obj.key, request)
        )
        s3_pending_upload_data = S3PendingUploadData(
            upload_id=multipart_upload.id, object_key=obj.key
        )
    elif isinstance(storage, FileSystemStorage):
        file = ContentFile("", name=file_name)
    else:
        raise ValueError(
            "TusUpload is only supported for S3Storage and FileSystemStorage"
        )
    tus_upload = await TusUpload.objects.acreate(
        created_by=user,
        file=file,
        total_size=total_size,
        completion_hook=completion_hook,
        completion_hook_parameters=completion_hook_parameters,
        pending_upload_data=s3_pending_upload_data,
    )
    return await process_new_tus_content(tus_upload, request, content_size, storage)


async def get_tus_upload(tus_upload_id: UUID) -> TusUpload:
    qs = TusUpload.objects.all().select_related("created_by")
    return await qs.aget(id=tus_upload_id)


async def store_tus_s3_content(
    tus_upload: TusUpload, stream: LazyStream, last_write: bool, storage: Storage
) -> int:
    written_bytes = 0
    multipart_upload = storage.bucket.Object(
        tus_upload.pending_upload_data["object_key"]
    ).MultipartUpload(tus_upload.pending_upload_data["upload_id"])
    try:
        uploaded_parts = [
            S3Part(ETag=part.e_tag, PartNumber=part.part_number)
            for part in multipart_upload.parts.all()
        ]
    except storage.connection.meta.client.exceptions.NoSuchUpload as e:
        storage.delete(tus_upload.pending_upload_data["object_key"])
        await tus_upload.adelete()
        raise api_ex.NotFoundError()  # TODO use other exception and catch and raise API exception in api

    for chunk in stream:
        part = multipart_upload.Part(len(uploaded_parts) + 1)
        part_response = part.upload(Body=chunk)
        uploaded_parts.append(
            S3Part(ETag=part_response["ETag"], PartNumber=part.part_number)
        )
        written_bytes += len(chunk)

    if last_write:
        # Never complete upload if new offset is not saved
        await transaction_on_commit_async(multipart_upload.complete)(
            MultipartUpload={"Parts": uploaded_parts}
        )
        tus_upload.file = multipart_upload.object_key
    ## TODO use multipart_upload.abort in error scenario
    return written_bytes


def store_tus_file_content(tus_upload: TusUpload, stream: LazyStream) -> int:
    written_bytes = 0
    with tus_upload.file.open("w+b") as file:
        for chunk in stream:
            written_bytes += file.write(chunk)
    return written_bytes


@transaction_atomic_async
async def store_tus_content(
    tus_upload: TusUpload, stream: LazyStream, last_write: bool, storage: Storage
):
    if isinstance(storage, S3Storage):
        written_bytes = await store_tus_s3_content(
            tus_upload, stream, last_write, storage
        )
    elif isinstance(storage, FileSystemStorage):
        written_bytes = store_tus_file_content(tus_upload, stream)
    else:
        raise ValueError(
            "TusUpload is only supported for S3Storage and FileSystemStorage"
        )
    tus_upload.offset += written_bytes
    await tus_upload.asave()


async def process_new_tus_content(
    tus_upload: TusUpload,
    request: HttpRequest,
    content_size: int,
    storage: Storage = None,
) -> TusUpload:
    if storage is None:
        file_field = TusUpload._meta.get_field("file")
        storage = file_field.storage
    last_write = content_size + tus_upload.offset == tus_upload.total_size
    if content_size:
        if content_size + tus_upload.offset > tus_upload.total_size:
            raise api_ex.ContentTooLarge()  # TODO use other exception and catch and raise API exception in api
        chunk_size = (
            ChunksizeAdjuster().adjust_chunksize(8 * 1024 * 1024, tus_upload.total_size)
            if isinstance(storage, S3Storage)
            else File.DEFAULT_CHUNK_SIZE
        )
        stream = LazyStream(ChunkIter(request, chunk_size))
        await store_tus_content(
            tus_upload=tus_upload, stream=stream, last_write=last_write, storage=storage
        )

    if last_write:
        completion_hook = import_string(tus_upload.completion_hook)
        if not iscoroutinefunction(completion_hook):
            # we're in an async context so if the function call any db operation we need this
            completion_hook = sync_to_async(completion_hook)
        await completion_hook(
            **tus_upload.completion_hook_parameters, tus_upload=tus_upload
        )
        # TODO handle move of file
        # don't call tus_upload.adelete directly since it will set id to None and we need it for tus headers
        await TusUpload.objects.filter(id=tus_upload.id).adelete()
    return tus_upload
