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

from typing import Any

from pydantic import BaseModel, Field


class ImageSettings(BaseModel):
    THUMBNAIL_PROJECT_LOGO_SMALL: str = "32x32_crop"
    THUMBNAIL_PROJECT_LOGO_LARGE: str = "80x80_crop"
    VALID_CONTENT_TYPES: list[str] = Field(
        default=[
            "image/jpeg",
            "image/png",
            "image/gif",
            "image/webp",
        ]
    )
    # easy_thumbnails
    THUMBNAIL_ALIASES: dict[str, Any] = Field(
        default={
            "": {
                "32x32_crop": {"size": (32, 32), "crop": True},
                "80x80_crop": {"size": (80, 80), "crop": True},
            }
        },
        exclude=True,
    )
