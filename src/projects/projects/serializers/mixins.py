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

from pathlib import Path

from django.conf import settings
from pydantic import model_validator

from base.serializers import BaseModel, FileField
from base.utils.concurrency import run_async_as_sync


# TODO : extract build of logo_small and logo_large from class
class ProjectLogoBaseSerializer(BaseModel):
    logo: FileField | None = None
    logo_small: str | None = None
    logo_large: str | None = None

    @model_validator(mode="after")
    def resolve_logo_computed(self):
        from projects.projects.services import (
            get_logo_large_thumbnail_url,
            get_logo_small_thumbnail_url,
        )

        if self.logo:
            logo_path = (
                Path(settings.MEDIA_ROOT, self.logo.path)
                .__str__()
                .replace("/media/", "")
            )
            self.logo_small = run_async_as_sync(get_logo_small_thumbnail_url(logo_path))
            self.logo_large = run_async_as_sync(get_logo_large_thumbnail_url(logo_path))
        return self
