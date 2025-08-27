# -*- coding: utf-8 -*-
# Copyright (C) 2024-2025 BIRU
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

from tests.utils import factories as f
from tests.utils.bad_params import NOT_EXISTING_REF

pytestmark = pytest.mark.django_db


##########################################################
# GET /projects/<id>/stories/<ref>/assignments
##########################################################


async def test_create_story_assignment_invalid_story(client, project_template):
    project = await f.create_project(project_template)
    await f.create_story(project=project)

    data = {"user_id": project.created_by.b64id}

    client.login(project.created_by)
    response = await client.post(
        f"/projects/{project.b64id}/stories/{NOT_EXISTING_REF}/assignments", json=data
    )
    assert response.status_code == 404, response.data


async def test_create_story_assignment_user_without_permissions(
    client, project_template
):
    project = await f.create_project(project_template)
    story = await f.create_story(project=project)
    user = await f.create_user()

    data = {"user_id": project.created_by.b64id}

    client.login(user)
    response = await client.post(
        f"/projects/{project.b64id}/stories/{story.ref}/assignments", json=data
    )
    assert response.status_code == 403, response.data


async def test_create_story_assignment_ok(client, project_template):
    project = await f.create_project(project_template)
    story = await f.create_story(project=project)

    data = {"user_id": project.created_by.b64id}

    client.login(project.created_by)
    response = await client.post(
        f"/projects/{project.b64id}/stories/{story.ref}/assignments", json=data
    )
    assert response.status_code == 200, response.data["data"]


##########################################################
# DELETE /projects/<id>/stories/<ref>/assignments/<user_id>
##########################################################


async def test_delete_story_assignment_invalid_story(client, project_template):
    pj_admin = await f.create_user()
    project = await f.create_project(project_template, created_by=pj_admin)
    story = await f.create_story(project=project)
    await f.create_story_assignment(story=story, user=pj_admin)

    client.login(pj_admin)
    response = await client.delete(
        f"/projects/{project.b64id}/stories/{NOT_EXISTING_REF}/assignments/{pj_admin.b64id}"
    )
    assert response.status_code == 404, response.data


async def test_delete_story_assignment_user_without_permissions(
    client, project_template
):
    user = await f.create_user()
    pj_admin = await f.create_user()
    project = await f.create_project(project_template, created_by=pj_admin)
    story = await f.create_story(project=project)
    await f.create_story_assignment(story=story, user=pj_admin)

    client.login(user)
    response = await client.delete(
        f"/projects/{project.b64id}/stories/{story.ref}/assignments/{pj_admin.b64id}"
    )
    assert response.status_code == 403, response.data


async def test_delete_story_assignment_user_not_assigned(client, project_template):
    user = await f.create_user()
    pj_admin = await f.create_user()
    project = await f.create_project(project_template, created_by=pj_admin)
    story = await f.create_story(project=project)
    await f.create_story_assignment(story=story, user=pj_admin)

    client.login(pj_admin)
    response = await client.delete(
        f"/projects/{project.b64id}/stories/{story.ref}/assignments/{user.b64id}"
    )
    assert response.status_code == 404, response.data


async def test_delete_story_assignment_ok(client, project_template):
    pj_admin = await f.create_user()
    project = await f.create_project(project_template, created_by=pj_admin)
    story = await f.create_story(project=project)
    await f.create_story_assignment(story=story, user=pj_admin)

    client.login(pj_admin)
    response = await client.delete(
        f"/projects/{project.b64id}/stories/{story.ref}/assignments/{pj_admin.b64id}"
    )
    assert response.status_code == 204, response.data
