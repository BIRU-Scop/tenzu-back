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
from fastapi import status

from tests.utils import factories as f

pytestmark = pytest.mark.django_db(transaction=True)

WRONG_REF = 9999


##########################################################
# GET /projects/<id>/stories/<ref>/assignments
##########################################################


async def test_create_story_assignment_invalid_story(client):
    project = await f.create_project()
    await f.create_story(project=project)

    data = {"username": project.created_by.username}

    client.login(project.created_by)
    response = client.post(f"/projects/{project.b64id}/stories/{WRONG_REF}/assignments", json=data)
    assert response.status_code == status.HTTP_404_NOT_FOUND, response.text


async def test_create_story_assignment_user_without_permissions(client):
    project = await f.create_project()
    story = await f.create_story(project=project)
    user = await f.create_user()

    data = {"username": project.created_by.username}

    client.login(user)
    response = client.post(f"/projects/{project.b64id}/stories/{story.ref}/assignments", json=data)
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.text


async def test_create_story_assignment_ok(client):
    project = await f.create_project()
    story = await f.create_story(project=project)

    data = {"username": project.created_by.username}

    client.login(project.created_by)
    response = client.post(f"/projects/{project.b64id}/stories/{story.ref}/assignments", json=data)
    assert response.status_code == status.HTTP_200_OK, response.text


##########################################################
# DELETE /projects/<id>/stories/<ref>/assignments/<username>
##########################################################


async def test_delete_story_assignment_invalid_story(client):
    pj_admin = await f.create_user()
    project = await f.create_project(created_by=pj_admin)
    story = await f.create_story(project=project)
    await f.create_story_assignment(story=story, user=pj_admin)

    client.login(pj_admin)
    response = client.delete(f"/projects/{project.b64id}/stories/{WRONG_REF}/assignments/{pj_admin.username}")
    assert response.status_code == status.HTTP_404_NOT_FOUND, response.text


async def test_delete_story_assignment_user_without_permissions(client):
    user = await f.create_user()
    pj_admin = await f.create_user()
    project = await f.create_project(created_by=pj_admin)
    story = await f.create_story(project=project)
    await f.create_story_assignment(story=story, user=pj_admin)

    client.login(user)
    response = client.delete(f"/projects/{project.b64id}/stories/{story.ref}/assignments/{pj_admin.username}")
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.text


async def test_delete_story_assignment_user_not_assigned(client):
    user = await f.create_user()
    pj_admin = await f.create_user()
    project = await f.create_project(created_by=pj_admin)
    story = await f.create_story(project=project)
    await f.create_story_assignment(story=story, user=pj_admin)

    client.login(pj_admin)
    response = client.delete(f"/projects/{project.b64id}/stories/{story.ref}/assignments/{user.username}")
    assert response.status_code == status.HTTP_404_NOT_FOUND, response.text


async def test_delete_story_assignment_ok(client):
    pj_admin = await f.create_user()
    project = await f.create_project(created_by=pj_admin)
    story = await f.create_story(project=project)
    await f.create_story_assignment(story=story, user=pj_admin)

    client.login(pj_admin)
    response = client.delete(f"/projects/{project.b64id}/stories/{story.ref}/assignments/{pj_admin.username}")
    assert response.status_code == status.HTTP_204_NO_CONTENT, response.text
