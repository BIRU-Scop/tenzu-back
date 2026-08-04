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
from django.conf import settings

from commons.exceptions import api as ex


def add_tus_headers(response, max_size: int | None = None):
    """
    Utility that adds the response headers expected by the tus protocol
    """
    response.headers["Tus-Resumable"] = settings.SUPPORTED_TUS_VERSION
    response.headers["Tus-Version"] = settings.SUPPORTED_TUS_VERSION
    response.headers["Tus-Extension"] = settings.SUPPORTED_TUS_EXTENSIONS
    if max_size is not None:
        response.headers["Tus-Max-Size"] = max_size
    # response.headers["Upload-Offset"] = "TODO"
    # response.header["Upload-Length"] = "TODO"
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
