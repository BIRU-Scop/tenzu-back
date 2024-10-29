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

from asgiref.sync import sync_to_async
from easy_thumbnails.exceptions import InvalidImageFormatError  # type: ignore
from easy_thumbnails.files import ThumbnailerFieldFile, get_thumbnailer  # type: ignore
from easy_thumbnails.source_generators import pil_image  # type: ignore
from ninja import UploadedFile

from configurations.conf import settings


def get_thumbnail(relative_image_path: str, thumbnailer_size: str) -> ThumbnailerFieldFile:
    try:
        thumbnailer = get_thumbnailer(relative_image_path)
        return thumbnailer[thumbnailer_size]

    except InvalidImageFormatError as e:
        return None


@sync_to_async
def get_thumbnail_url(relative_image_path: str, thumbnailer_size: str) -> str | None:
    thumbnail = get_thumbnail(relative_image_path, thumbnailer_size)

    if not thumbnail:
        return None

    return thumbnail.url


def valid_content_type(uploaded_img: UploadedFile) -> bool:
    return uploaded_img.content_type in settings.IMAGES.VALID_CONTENT_TYPES


def valid_image_content(uploaded_img: UploadedFile) -> bool:
    try:
        pil_image(uploaded_img.file)
        return True
    except Exception:
        return False
