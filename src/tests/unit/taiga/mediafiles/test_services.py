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

from unittest.mock import patch

from mediafiles import services
from tests.utils import factories as f


async def test_create_mediafiles():
    project = f.build_project()
    user = f.build_user()

    uploadfiles = [
        f.build_image_uploadfile(),
        f.build_image_uploadfile(),
    ]

    mediafiles = [
        f.build_mediafile(),
        f.build_mediafile(),
    ]

    with patch("mediafiles.services.mediafiles_repositories", autospec=True) as fake_mediafiles_repository:
        fake_mediafiles_repository.create_mediafiles.return_value = mediafiles
        data = await services.create_mediafiles(files=uploadfiles, project=project, object=None, created_by=user)
        fake_mediafiles_repository.create_mediafiles.assert_awaited_once_with(
            files=uploadfiles, project=project, object=None, created_by=user
        )
        assert len(data) == 2
