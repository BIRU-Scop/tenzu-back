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
from django.db.models import Model
from ninja import UploadedFile

from mediafiles import repositories as mediafiles_repositories
from mediafiles.models import Mediafile
from projects.projects.models import Project
from users.models import User


async def create_mediafiles(
    files: list[UploadedFile],
    project: Project,
    created_by: User,
    object: Model | None = None,
) -> list[Mediafile]:
    return await mediafiles_repositories.create_mediafiles(
        files=files,
        project=project,
        object=object,
        created_by=created_by,
    )
