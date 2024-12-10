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

import pytest

from mediafiles import repositories
from tests.utils import factories as f

pytestmark = pytest.mark.django_db


#############################################################
# create_mediafiles
#############################################################


async def test_create_mediafiles_not_associated_to_an_object():
    project = await f.create_project()
    user = await f.create_user()
    files = [
        f.build_image_uploadfile(name="test1"),
        f.build_string_uploadfile(name="tests2", content="tests"),
    ]

    mediafile = await repositories.create_mediafiles(
        files=files, project=project, created_by=user
    )
    assert len(mediafile) == 2
    assert await project.mediafiles.acount() == 2

    assert mediafile[0].name == files[0].filename
    assert mediafile[0].content_type == "image/png"
    assert mediafile[0].size == 145

    assert mediafile[1].name == files[1].filename
    assert mediafile[1].content_type == "text/plain"
    assert mediafile[1].size == 5


async def test_create_mediafiles_associated_to_an_object():
    project = await f.create_project()
    story = await f.create_story(project=project)
    user = await f.create_user()

    files = [
        f.build_image_uploadfile(name="test1"),
        f.build_string_uploadfile(name="test2", content="tests"),
    ]

    mediafile = await repositories.create_mediafiles(
        files=files,
        project=project,
        created_by=user,
        object=story,
    )
    assert len(mediafile) == 2
    assert await project.mediafiles.acount() == 2
    assert await story.mediafiles.acount() == 2

    assert mediafile[0].name == files[0].filename
    assert mediafile[0].content_type == "image/png"
    assert mediafile[0].size == 145

    assert mediafile[1].name == files[1].filename
    assert mediafile[1].content_type == "text/plain"
    assert mediafile[1].size == 5
