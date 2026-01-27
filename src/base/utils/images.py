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
from typing import Literal

from asgiref.sync import sync_to_async
from django.conf import settings
from django.db.models.fields.files import FieldFile
from easy_thumbnails.exceptions import InvalidImageFormatError  # type: ignore
from easy_thumbnails.files import ThumbnailFile, get_thumbnailer  # type: ignore
from easy_thumbnails.source_generators import pil_image  # type: ignore
from ninja import UploadedFile

logger = logging.getLogger(__name__)


ImageSizeFormat = Literal["small", "large", "original"]


def _patched_thumbnail_open(self, mode=None, *args, **kwargs):
    return ThumbnailFile.open(self, mode, *args, **kwargs) or self


@sync_to_async
def get_thumbnail(file: FieldFile, thumbnailer_size: str) -> ThumbnailFile | None:
    try:
        thumbnailer = get_thumbnailer(file)
        file = thumbnailer[thumbnailer_size]
    except (InvalidImageFormatError, OSError) as e:
        logger.error(
            f"Image error for file {file} with format {thumbnailer_size}: '{e}'"
        )
        return None
    else:
        # TODO monkeypatch needed because of https://github.com/SmileyChris/easy-thumbnails/issues/669
        #  remove once fixed
        file.open = _patched_thumbnail_open.__get__(file)
        return file


def valid_image_content_type(uploaded_img: UploadedFile) -> bool:
    return uploaded_img.content_type in settings.IMAGES.VALID_CONTENT_TYPES


def valid_image_content(uploaded_img: UploadedFile) -> bool:
    try:
        pil_image(uploaded_img.file)
        return True
    except Exception:
        return False
