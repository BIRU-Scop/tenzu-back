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
from datetime import timedelta
from uuid import UUID

from botocore.exceptions import ClientError
from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from django.utils.http import http_date
from django.views.decorators.cache import never_cache
from ninja import Header, Path, Router, Status
from ninja.decorators import decorate_view
from pydantic import NonNegativeInt
from redis.exceptions import LockError

from commons.exceptions import api as ex
from commons.exceptions.api.errors import (
    ERROR_RESPONSE_400,
    ERROR_RESPONSE_401,
    ERROR_RESPONSE_403,
    ERROR_RESPONSE_404,
    ERROR_RESPONSE_409,
    ERROR_RESPONSE_412,
    ERROR_RESPONSE_413,
    ERROR_RESPONSE_415,
    ERROR_RESPONSE_422,
    ERROR_RESPONSE_423,
    ERROR_RESPONSE_424,
)
from commons.storage import services as storage_services
from commons.storage.exceptions import (
    MisalignedOffsets,
    NoOngoingMultipartUploadError,
    OverflowExpectedSizeError,
)
from commons.storage.models import TusUpload
from commons.storage.permissions import TusUploadPermissionsCheck
from commons.utils import concurrency
from commons.validators import B64UUID
from permissions import check_permissions

storage_router = Router()


##########################################################
# tus protocol
##########################################################


@storage_router.api_operation(
    ["HEAD"],
    "/upload/{tus_upload_id}",
    url_name="upload.tus.info",
    summary="Check status of tus upload",
    response={
        200: None,
        400: ERROR_RESPONSE_400,
        401: ERROR_RESPONSE_401,
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        412: ERROR_RESPONSE_412,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
@decorate_view(never_cache)
async def check_tus_upload(
    request: HttpRequest,
    response: HttpResponse,
    tus_upload_id: Path[B64UUID],
    tus_resumable: Header[str] = "1.0.0",
) -> Status[None]:
    """
    Retrieve info about an ongoing tus upload
    """
    check_tus_request(request)
    tus_upload = await get_tus_upload_or_404(tus_upload_id=tus_upload_id)

    await check_permissions(
        permissions=TusUploadPermissionsCheck.VIEW.value,
        user=request.user,
        obj=tus_upload,
    )
    add_tus_headers(
        response, tus_upload, max_size=settings.STORAGE.IMPORTATION_MAX_UPLOAD_FILE_SIZE
    )
    return Status(200, None)


@storage_router.patch(
    "/upload/{tus_upload_id}",
    url_name="upload.tus.continue",
    summary="Continue an ongoing tus upload",
    response={
        204: None,
        400: ERROR_RESPONSE_400,
        401: ERROR_RESPONSE_401,
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        409: ERROR_RESPONSE_409,
        412: ERROR_RESPONSE_412,
        413: ERROR_RESPONSE_413,
        415: ERROR_RESPONSE_415,
        422: ERROR_RESPONSE_422,
        423: ERROR_RESPONSE_423,
        424: ERROR_RESPONSE_424,
    },
    by_alias=True,
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "application/offset+octet-stream": {
                    "schema": {"type": "string", "format": "binary"}
                }
            },
        }
    },
)
async def continue_tus_upload(
    request: HttpRequest,
    response: HttpResponse,
    tus_upload_id: Path[B64UUID],
    content_type: Header[str],
    upload_offset: Header[NonNegativeInt],
    content_length: Header[NonNegativeInt],
    tus_resumable: Header[str] = "1.0.0",
) -> Status[None]:
    """
    Continue a tus upload where it left of
    """
    check_tus_request(request)
    tus_upload = await get_tus_upload_or_404(tus_upload_id=tus_upload_id)

    await check_permissions(
        permissions=TusUploadPermissionsCheck.MODIFY.value,
        user=request.user,
        obj=tus_upload,
    )
    try:
        # prevent parallel write on the same file
        async with concurrency.aget_redis_lock(
            f"tus_upload_{tus_upload.b64id}",
            blocking_timeout=settings.STORAGE.TUS_UPLOAD_LOCK_TIMEOUT,
            ttl=settings.STORAGE.TUS_UPLOAD_LOCK_TTL,
        ):
            tus_upload = await storage_services.process_new_tus_content(
                tus_upload, upload_offset, request, content_length
            )
    except NoOngoingMultipartUploadError:
        raise ex.NotFoundError()
    except OverflowExpectedSizeError:
        raise ex.ContentTooLarge(headers={"Tus-Max-Size": tus_upload.total_size})
    except MisalignedOffsets:
        raise ex.ConflictError(
            f"Provided offset for TusUpload {tus_upload.id} is not equal to server's"
        )
    except ClientError as e:
        raise ex.FailedDependency("Request to S3 has failed") from e
    except LockError as e:
        raise ex.LockedError("Another operation in ongoing on this tus upload") from e
    add_tus_headers(
        response, tus_upload, max_size=settings.STORAGE.IMPORTATION_MAX_UPLOAD_FILE_SIZE
    )
    return Status(204, None)


@storage_router.delete(
    "/upload/{tus_upload_id}",
    url_name="upload.tus.delete",
    summary="Delete an ongoing tus upload",
    response={
        204: None,
        400: ERROR_RESPONSE_400,
        401: ERROR_RESPONSE_401,
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        412: ERROR_RESPONSE_412,
        422: ERROR_RESPONSE_422,
        423: ERROR_RESPONSE_423,
    },
    by_alias=True,
)
async def terminate_tus_upload(
    request: HttpRequest,
    response: HttpResponse,
    tus_upload_id: Path[B64UUID],
    tus_resumable: Header[str] = "1.0.0",
) -> Status[None]:
    """
    Terminate a tus upload and free up resources
    """
    check_tus_request(request)
    tus_upload = await get_tus_upload_or_404(tus_upload_id=tus_upload_id)

    await check_permissions(
        permissions=TusUploadPermissionsCheck.DELETE.value,
        user=request.user,
        obj=tus_upload,
    )
    try:
        # prevent parallel write on the same file
        async with concurrency.aget_redis_lock(
            f"tus_upload_{tus_upload.b64id}",
            blocking_timeout=settings.STORAGE.TUS_UPLOAD_LOCK_TIMEOUT,
            ttl=settings.STORAGE.TUS_UPLOAD_LOCK_TTL,
        ):
            await storage_services.delete_tus_upload(tus_upload)
    except LockError as e:
        raise ex.LockedError("Another operation in ongoing on this tus upload") from e
    return Status(204, None)


##########################################################
# misc
##########################################################


async def get_tus_upload_or_404(tus_upload_id: UUID) -> TusUpload:
    try:
        tus_upload = await storage_services.get_tus_upload(tus_upload_id=tus_upload_id)
    except TusUpload.DoesNotExist:
        raise ex.NotFoundError(f"TusUpload {tus_upload_id} does not exist")

    return tus_upload


def add_tus_headers(
    response: HttpResponse, tus_upload: TusUpload, max_size: int | None = None
):
    """
    Utility that adds the response headers expected by the tus protocol
    """
    response.headers["Tus-Resumable"] = settings.SUPPORTED_TUS_VERSION
    response.headers["Tus-Version"] = settings.SUPPORTED_TUS_VERSION
    response.headers["Tus-Extension"] = settings.SUPPORTED_TUS_EXTENSIONS
    if max_size is not None:
        response.headers["Tus-Max-Size"] = max_size
    response.headers["Upload-Offset"] = tus_upload.offset
    response.headers["Upload-Length"] = tus_upload.total_size
    response.headers["Location"] = reverse(
        f"api-{settings.API_VERSION}:upload.tus.continue",
        kwargs={"tus_upload_id": tus_upload.b64id},
    )
    expiry_date = tus_upload.created_at + timedelta(
        hours=settings.STORAGE.TUS_UPLOAD_EXPIRATION
    )
    response.headers["Upload-Expires"] = http_date(expiry_date.timestamp())


def check_tus_request(request, max_size: int | None = None):
    """
    Utility that check the specified tus parameters are correct
    """
    version_header = request.headers.get("Tus-Resumable")
    if version_header != settings.SUPPORTED_TUS_VERSION:
        raise ex.PreconditionFailed(
            "Unsupported tus version",
            headers={"Tus-Version": settings.SUPPORTED_TUS_VERSION},
        )
    length_header = request.headers.get("Upload-Length")
    if max_size is not None and length_header is not None:
        try:
            if int(length_header) > max_size:
                raise ex.ContentTooLarge(headers={"Tus-Max-Size": max_size})
        except ValueError:
            pass  # error will be caught by ninja validation
        content_header = request.headers.get("Content-Length")
        try:
            if int(content_header) > int(length_header):
                raise ex.BadRequest("Content size can't be bigger than total size")
        except ValueError:
            pass  # error will be caught by ninja validation
    type_header = request.headers.get("Content-Type")
    if type_header is not None and type_header != "application/offset+octet-stream":
        raise ex.UnsupportedMediaType(
            "Content type must be 'application/offset+octet-stream'"
        )
