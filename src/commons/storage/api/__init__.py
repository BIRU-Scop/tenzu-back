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

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.views.decorators.cache import never_cache
from exceptions.api.errors import (
    ERROR_RESPONSE_400,
    ERROR_RESPONSE_403,
    ERROR_RESPONSE_404,
    ERROR_RESPONSE_412,
)
from ninja import Header, Path, Router, Status
from ninja.decorators import decorate_view
from validators import B64UUID

from commons.exceptions import api as ex
from commons.storage import services as storage_services
from commons.storage.models import TusUpload
from commons.storage.permissions import TusUploadPermissionsCheck
from permissions import check_permissions

storage_router = Router()


##########################################################
# tus protocol
##########################################################


@storage_router.api_operation(
    ["HEAD"],
    "/upload/{tus_upload_id}",
    url_name="upload.tus.head",
    summary="Check status of tus upload",
    response={
        200: None,
        400: ERROR_RESPONSE_400,
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        412: ERROR_RESPONSE_412,
    },
    by_alias=True,
)
@decorate_view(never_cache)
async def check_tus_upload(
    request: HttpRequest,
    response: HttpResponse,
    tus_upload_id: Path[B64UUID],
    tus_resumable: Header[str],
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
    add_tus_headers(response, tus_upload=tus_upload)
    return Status(200, None)


# TODO PATCH


##########################################################
# misc
##########################################################


async def get_tus_upload_or_404(tus_upload_id: UUID) -> TusUpload:
    try:
        tus_upload = await storage_services.get_tus_upload(tus_upload_id=tus_upload_id)
    except TusUpload.DoesNotExist:
        raise ex.NotFoundError(f"TusUpload {tus_upload_id} does not exist")

    return tus_upload


def add_tus_headers(response, tus_upload: TusUpload, max_size: int | None = None):
    """
    Utility that adds the response headers expected by the tus protocol
    """
    response.headers["Tus-Resumable"] = settings.SUPPORTED_TUS_VERSION
    response.headers["Tus-Version"] = settings.SUPPORTED_TUS_VERSION
    response.headers["Tus-Extension"] = settings.SUPPORTED_TUS_EXTENSIONS
    if max_size is not None:
        response.headers["Tus-Max-Size"] = max_size
    response.headers["Upload-Offset"] = tus_upload.offset
    response.header["Upload-Length"] = tus_upload.total_size
    # response.header["Location"] = "TODO"
    # response.header["Upload-Expires"] = "TODO"


def check_tus_request(request, max_size: int | None = None):
    """
    Utility that check the specified tus parameters are correct
    """
    version_header = request.headers.get("Tus-Resumable")
    if version_header is not None and version_header != settings.SUPPORTED_TUS_VERSION:
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
    type_header = request.headers.get("Content-Type")
    if type_header is not None and type_header != "application/offset+octet-stream":
        raise ex.UnsupportedMediaType(
            "Content type must be 'application/offset+octet-stream'"
        )
