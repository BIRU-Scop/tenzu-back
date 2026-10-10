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
import logging
from datetime import datetime
from functools import partial
from typing import TypedDict
from uuid import UUID

from asgiref.sync import iscoroutinefunction, sync_to_async
from botocore.exceptions import ClientError
from django.core.files import File
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage, Storage
from django.core.files.utils import validate_file_name
from django.db import transaction
from django.db.models.deletion import RestrictedError
from django.http import HttpRequest
from django.http.multipartparser import ChunkIter, LazyStream, MultiPartParser
from django.utils.module_loading import import_string
from s3transfer.utils import MIN_UPLOAD_CHUNKSIZE, ChunksizeAdjuster
from storages.backends.s3 import S3Storage

from commons.storage import exceptions as ex
from commons.storage.models import (
    S3Part,
    S3PendingUploadData,
    StoragedObject,
    TusUpload,
)
from commons.utils.async_func import (
    transaction_atomic_async,
    transaction_on_commit_async,
)
from commons.utils.iterators import min_chunk_lazystream
from ninja_jwt.utils import aware_utcnow
from users.models import User

logger = logging.getLogger(__name__)

##########################################################
# filters and querysets
##########################################################


class StoragedObjectFilters(TypedDict, total=False):
    id: UUID
    deleted_at__lt: datetime


class TusUploadFilters(TypedDict, total=False):
    id: UUID
    created_at__lt: datetime


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
    except RestrictedError as e:
        # This happens when you try to delete a StoragedObject that is being used by someone
        # (using ForeignKey with on_delete=PROTECT).
        logger.warning(
            f"{storaged_object.__class__.__name__} {storaged_object.id} could not be deleted: {e}"
        )
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
    overwrite_base_path: str | None = None,
) -> TusUpload:
    file_field = TusUpload._meta.get_field("file")
    storage = file_field.storage
    file_name = MultiPartParser.sanitize_file_name(None, file_name)

    tus_upload = TusUpload(
        created_by=user,
        file=None,
        total_size=total_size,
        completion_hook=completion_hook,
        completion_hook_parameters=completion_hook_parameters,
        pending_upload_data={},
    )
    if overwrite_base_path is not None:
        tus_upload.set_upload_to_base_path(overwrite_base_path)

    if isinstance(storage, S3Storage):
        name = file_field.generate_filename(tus_upload, file_name)
        validate_file_name(name, allow_relative_path=True)
        # Potentially find a different name depending on storage constraints.
        name = storage.get_available_name(name, max_length=file_field.max_length)
        # Validate the (potentially) new name.
        validate_file_name(name, allow_relative_path=True)

        obj = storage._open(name, "w+b").obj

        multipart_upload = obj.initiate_multipart_upload(
            **storage._get_write_parameters(obj.key, request)
        )
        tus_upload.pending_upload_data = S3PendingUploadData(
            upload_id=multipart_upload.id, object_key=obj.key
        )
    elif isinstance(storage, FileSystemStorage):
        tus_upload.file = ContentFile("", name=file_name)
    else:
        raise ValueError(
            "TusUpload is only supported for S3Storage and FileSystemStorage"
        )
    await tus_upload.asave()
    return await process_new_tus_content(tus_upload, request, content_size, storage)


##########################################################
# retrieve tus upload
##########################################################


async def get_tus_upload(tus_upload_id: UUID) -> TusUpload:
    qs = TusUpload.objects.all().select_related("created_by")
    return await qs.aget(id=tus_upload_id)


def list_tus_uploads(
    filters: TusUploadFilters = {},
) -> list[TusUpload]:
    qs = TusUpload.objects.all().filter(**filters)
    return list(qs)


##########################################################
# process tus upload
##########################################################


def _check_stored_length(tus_upload: TusUpload, written_bytes: int):
    # prevent any write as soon as what was sent overflow expected max size
    if tus_upload.offset + written_bytes > tus_upload.total_size:
        tus_upload.offset += written_bytes
        tus_upload.save()
        raise ex.OverflowExpectedSizeError()


def _complete_s3_upload(
    tus_upload: TusUpload, multipart_upload, uploaded_parts: list[S3Part]
):
    try:
        multipart_upload.complete(MultipartUpload={"Parts": uploaded_parts})
    except ClientError as e:
        logger.error(e)
        delete_tus_upload(tus_upload)
        raise e


def store_tus_s3_content(
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
    except ClientError as e:
        if type(e).__name__ == "NoSuchUpload":
            storage.delete(tus_upload.pending_upload_data["object_key"])
            tus_upload.delete()
            raise ex.NoOngoingMultipartUploadError()
        else:
            raise e

    for chunk in min_chunk_lazystream(
        stream, min_size=None if last_write else MIN_UPLOAD_CHUNKSIZE
    ):
        part = multipart_upload.Part(len(uploaded_parts) + 1)
        try:
            part_response = part.upload(Body=chunk)
        except ClientError as e:
            logger.error(e)
            delete_tus_upload(tus_upload)
            raise e
        uploaded_parts.append(
            S3Part(ETag=part_response["ETag"], PartNumber=part.part_number)
        )
        written_bytes += len(chunk)
        _check_stored_length(tus_upload, written_bytes)

    if last_write:
        # Never complete upload if new offset is not saved
        transaction.on_commit(
            partial(
                _complete_s3_upload,
                tus_upload=tus_upload,
                multipart_upload=multipart_upload,
                uploaded_parts=uploaded_parts,
            )
        )
        tus_upload.file = multipart_upload.object_key
    return written_bytes


def store_tus_file_content(tus_upload: TusUpload, stream: LazyStream) -> int:
    written_bytes = 0
    with tus_upload.file.open("r+b") as file:
        file.seek(tus_upload.offset)
        for chunk in stream:
            written_bytes += file.write(chunk)
            _check_stored_length(tus_upload, written_bytes)
    return written_bytes


@transaction.atomic()
def store_tus_content(
    tus_upload: TusUpload, stream: LazyStream, last_write: bool, storage: Storage
):
    if isinstance(storage, S3Storage):
        written_bytes = store_tus_s3_content(tus_upload, stream, last_write, storage)
    elif isinstance(storage, FileSystemStorage):
        written_bytes = store_tus_file_content(tus_upload, stream)
    else:
        raise ValueError(
            "TusUpload is only supported for S3Storage and FileSystemStorage"
        )
    tus_upload.offset += written_bytes
    tus_upload.save()


async def process_new_tus_content(
    tus_upload: TusUpload,
    request: HttpRequest,
    content_size: int,
    storage: Storage = None,
) -> TusUpload:
    if content_size + tus_upload.offset > tus_upload.total_size:
        raise ex.OverflowExpectedSizeError()
    if storage is None:
        file_field = TusUpload._meta.get_field("file")
        storage = file_field.storage
    last_write = content_size + tus_upload.offset == tus_upload.total_size
    if content_size:
        chunk_size = (
            ChunksizeAdjuster().adjust_chunksize(8 * 1024 * 1024, tus_upload.total_size)
            if isinstance(storage, S3Storage)
            else File.DEFAULT_CHUNK_SIZE
        )
        stream = LazyStream(ChunkIter(request, chunk_size), length=content_size)
        await sync_to_async(store_tus_content)(
            tus_upload=tus_upload, stream=stream, last_write=last_write, storage=storage
        )

    if last_write:
        completion_hook = import_string(tus_upload.completion_hook)
        if not iscoroutinefunction(completion_hook):
            # we're in an async context so if the function call any db operation we need this
            completion_hook = sync_to_async(completion_hook)
        # Responsibility for the file itself passes to the hook function
        # The hook should either delete it after using it or store a reference to it in another db model
        await completion_hook(
            **tus_upload.completion_hook_parameters, tus_upload=tus_upload
        )
        # don't call tus_upload.adelete directly since it will set id to None and we need it for tus headers
        await TusUpload.objects.filter(id=tus_upload.id).adelete()
    return tus_upload


##########################################################
# delete tus upload
##########################################################


@transaction.atomic
def delete_tus_upload(
    tus_upload: TusUpload,
) -> bool:
    try:
        with transaction.atomic():
            tus_upload.delete()
    except RestrictedError as e:
        # This happens when you try to delete a TusUpload that is being used by someone
        # (using ForeignKey with on_delete=PROTECT).
        logger.warning(
            f"{tus_upload.__class__.__name__} {tus_upload.id} could not be deleted: {e}"
        )
        return False
    else:
        if tus_upload.file:
            transaction.on_commit(partial(tus_upload.file.delete, save=False))
        else:
            file_field = TusUpload._meta.get_field("file")
            storage = file_field.storage
            if isinstance(storage, S3Storage):
                multipart_upload = storage.bucket.Object(
                    tus_upload.pending_upload_data["object_key"]
                ).MultipartUpload(tus_upload.pending_upload_data["upload_id"])
                try:
                    multipart_upload.abort()
                except ClientError as e:
                    pass
                try:
                    storage.delete(tus_upload.pending_upload_data["object_key"])
                except ClientError as e:
                    pass
        return True
