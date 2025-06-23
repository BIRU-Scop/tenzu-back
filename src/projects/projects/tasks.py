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
import shutil
from pathlib import Path

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from procrastinate.contrib.django import app
from storages.backends.s3 import S3Storage

from projects.projects.models import Project


@app.task
async def delete_old_logo(file_name: str) -> None:
    # we need to delete parent folder to also delete any created thumbnails
    path = str(Path(file_name).parent)
    storage = Project._meta.get_field("logo").storage

    if isinstance(storage, S3Storage):
        storage.bucket.objects.filter(Prefix=path).delete()
    elif isinstance(storage, FileSystemStorage):
        path = Path(settings.MEDIA_ROOT, path)
        shutil.rmtree(str(path))
    else:
        raise ValueError(
            "Deletion is only supported for S3Storage and FileSystemStorage"
        )
