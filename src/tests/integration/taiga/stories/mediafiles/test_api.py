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
from django.core.files.uploadedfile import SimpleUploadedFile

from tests.utils import factories as f
from tests.utils.bad_params import (
    INVALID_B64ID,
    NOT_EXISTING_B64ID,
    NOT_EXISTING_REF,
)

pytestmark = pytest.mark.django_db


##########################################################
# POST /projects/<b64id>/stories/<ref>/stories/mediafiles
##########################################################


async def test_create_story_mediafile_200_ok(client, project_template):
    project = await f.create_project(project_template)
    story = await f.create_story(project=project)
    user = project.created_by
    file1 = f.build_image_file("image1")
    file2 = f.build_image_file("image2")
    file3 = f.build_image_file("image3")

    files = [
        ("files", (file1.name, file1, "image/png")),
        ("files", (file2.name, file2, "image/png")),
        ("files", (file3.name, file3, "image/png")),
    ]

    client.login(user)
    response = await client.post(
        f"/projects/{project.b64id}/stories/{story.ref}/mediafiles",
        FILES=files,
    )
    assert response.status_code == 200, response.data
    assert len(response.json()) == 3


async def test_create_story_mediafile_403_forbidden_error_no_permissions(
    client, project_template
):
    project = await f.create_project(project_template)
    story = await f.create_story(project=project)
    user = await f.create_user()
    files = {"file": SimpleUploadedFile("test.txt", b"data345")}

    client.login(user)
    response = await client.post(
        f"/projects/{project.b64id}/stories/{story.ref}/mediafiles",
        FILES=files,
    )
    assert response.status_code == 403, response.data


async def test_create_story_mediafile_404_not_found_project_b64id(
    client, project_template
):
    project = await f.create_project(project_template)
    story = await f.create_story(project=project)
    user = project.created_by
    files = {"file": SimpleUploadedFile("test.txt", b"data345")}

    client.login(user)
    response = await client.post(
        f"/projects/{NOT_EXISTING_B64ID}/stories/{story.ref}/mediafiles",
        FILES=files,
    )
    assert response.status_code == 404, response.data


async def test_create_story_mediafile_404_not_found_story_ref(client, project_template):
    project = await f.create_project(project_template)
    user = project.created_by
    files = {"file": SimpleUploadedFile("test.txt", b"data345")}

    client.login(user)
    response = await client.post(
        f"/projects/{project.b64id}/stories/{NOT_EXISTING_REF}/mediafiles",
        FILES=files,
    )
    assert response.status_code == 404, response.data


async def test_create_story_mediafile_422_unprocessable_entity_project_b64id(
    client, project_template
):
    project = await f.create_project(project_template)
    story = await f.create_story(project=project)
    user = project.created_by
    files = {"file": SimpleUploadedFile("test.txt", b"data345")}

    client.login(user)
    response = await client.post(
        f"/projects/{INVALID_B64ID}/stories/{story.ref}/mediafiles",
        FILES=files,
    )
    assert response.status_code == 422, response.data


async def test_create_story_mediafile_422_unprocessable_entity_bad_request(
    client, project_template
):
    project = await f.create_project(project_template)
    story = await f.create_story(project=project)
    user = project.created_by

    client.login(user)
    response = await client.post(
        f"/projects/{project.b64id}/stories/{story.ref}/mediafiles",
    )
    assert response.status_code == 422, response.data
