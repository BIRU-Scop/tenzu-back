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
from asgiref.sync import sync_to_async
from fastapi import status

from attachments import repositories as attachments_repositories
from tests.utils import factories as f
from tests.utils.bad_params import (
    INVALID_B64ID,
    INVALID_REF,
    NOT_EXISTING_B64ID,
    NOT_EXISTING_REF,
)

pytestmark = pytest.mark.django_db(transaction=True)


##########################################################
# POST /projects/<b64id>/stories/<ref>/stories/attachments
##########################################################


async def test_create_story_attachment_200_ok(client):
    project = await f.create_project()
    story = await f.create_story(project=project)
    user = project.created_by
    file = f.build_image_file("image1")

    files = [
        ("file", (file.name, file, "image/png")),
    ]

    client.login(user)
    response = client.post(
        f"/projects/{project.b64id}/stories/{story.ref}/attachments",
        files=files,
    )
    assert response.status_code == status.HTTP_200_OK, response.text


async def test_create_story_attachment_403_forbidden_error_no_permissions(client):
    project = await f.create_project(public_permissions=[])
    story = await f.create_story(project=project)
    user = await f.create_user()
    file = f.build_image_file("image")

    files = [
        ("file", (file.name, file, "image/png")),
    ]

    client.login(user)
    response = client.post(
        f"/projects/{project.b64id}/stories/{story.ref}/attachments",
        files=files,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.text


async def test_create_story_attachment_404_not_found_project_b64id(client):
    project = await f.create_project()
    story = await f.create_story(project=project)
    user = project.created_by
    file = f.build_image_file("image")

    files = [
        ("file", (file.name, file, "image/png")),
    ]

    client.login(user)
    response = client.post(
        f"/projects/{NOT_EXISTING_B64ID}/stories/{story.ref}/attachments",
        files=files,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND, response.text


async def test_create_story_attachment_404_not_found_story_ref(client):
    project = await f.create_project()
    user = project.created_by
    file = f.build_image_file("image")

    files = [
        ("file", (file.name, file, "image/png")),
    ]

    client.login(user)
    response = client.post(
        f"/projects/{project.b64id}/stories/{NOT_EXISTING_REF}/attachments",
        files=files,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND, response.text


async def test_create_story_attachment_422_unprocessable_entity_project_b64id(client):
    project = await f.create_project()
    story = await f.create_story(project=project)
    user = project.created_by
    file = f.build_image_file("image")

    files = [
        ("file", (file.name, file, "image/png")),
    ]

    client.login(user)
    response = client.post(
        f"/projects/{INVALID_B64ID}/stories/{story.ref}/attachments",
        files=files,
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, response.text


async def test_create_story_attachment_422_unprocessable_entity_story_ref(client):
    project = await f.create_project()
    user = project.created_by
    file = f.build_image_file("image")

    files = [
        ("file", (file.name, file, "image/png")),
    ]

    client.login(user)
    response = client.post(
        f"/projects/{project.b64id}/stories/{INVALID_REF}/attachments",
        files=files,
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, response.text


async def test_create_story_attachment_422_unprocessable_entity_bad_request(client):
    project = await f.create_project()
    story = await f.create_story(project=project)
    user = project.created_by

    client.login(user)
    response = client.post(
        f"/projects/{project.b64id}/stories/{story.ref}/attachments",
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, response.text


##########################################################
# GET projects/<id>/stories/<ref>/attachments
##########################################################


async def test_list_story_attachments_200_ok(client):
    project = await f.create_project()
    story = await f.create_story(project=project)
    user = project.created_by
    await f.create_attachment(content_object=story, created_by=user)
    await f.create_attachment(content_object=story, created_by=user)

    client.login(user)
    response = client.get(f"/projects/{project.b64id}/stories/{story.ref}/attachments")
    assert response.status_code == status.HTTP_200_OK, response.text
    assert len(response.json()) == 2


async def test_list_story_attachments_404_not_found_project(client):
    user = await f.create_user()

    client.login(user)
    response = client.get(f"/projects/{NOT_EXISTING_B64ID}/stories/1/attachments")
    assert response.status_code == status.HTTP_404_NOT_FOUND, response.text


async def test_list_story_attachments_404_not_found_story(client):
    project = await f.create_project()
    user = project.created_by

    client.login(user)
    response = client.get(
        f"/projects/{project.b64id}/stories/{NOT_EXISTING_REF}/attachments"
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND, response.text


async def test_list_story_attachments_403_forbidden_no_permissions(client):
    not_allowed_user = await f.create_user()
    project = await f.create_project()
    story = await f.create_story(project=project)

    client.login(not_allowed_user)
    response = client.get(f"/projects/{project.b64id}/stories/{story.ref}/attachments")
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.text


##########################################################
# DELETE projects/<id>/stories/<ref>/attachments/<id>
##########################################################


async def test_delete_story_attachments_204_no_content(client):
    project = await f.create_project()
    user = project.created_by
    story = await f.create_story(project=project)
    attachment = await f.create_attachment(content_object=story, created_by=user)

    assert (
        await attachments_repositories.get_attachment(filters={"id": attachment.id})
        == attachment
    )
    client.login(user)
    response = client.delete(
        f"/projects/{story.project.b64id}/stories/{story.ref}/attachments/{attachment.b64id}"
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT, response.text


async def test_delete_story_attachment_403_forbidden_no_permissions(client):
    project = await f.create_project()
    generic_role = await project.roles.aget(is_admin=False)
    member_user = await f.create_user()
    await f.create_project_membership(user=member_user, role=generic_role)
    story = await f.create_story(project=project)
    attachment = await f.create_attachment(content_object=story, created_by=member_user)

    assert (
        await attachments_repositories.get_attachment(filters={"id": attachment.id})
        == attachment
    )

    # now member_user can't modify story permissions
    generic_role.permissions = ["view_story"]
    await sync_to_async(generic_role.save)()

    client.login(member_user)
    response = client.delete(
        f"/projects/{story.project.b64id}/stories/{story.ref}/attachments/{attachment.b64id}"
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.text
    assert (
        await attachments_repositories.get_attachment(filters={"id": attachment.id})
        == attachment
    )


async def test_delete_story_attachments_404_not_found_nonexistent_project(client):
    user = await f.create_user()

    client.login(user)
    response = client.delete(
        f"/projects/{NOT_EXISTING_B64ID}/stories/{NOT_EXISTING_REF}/attachments/{NOT_EXISTING_B64ID}"
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND, response.text


async def test_delete_story_attachments_404_not_found_nonexistent_story(client):
    project = await f.create_project()

    client.login(project.created_by)
    response = client.delete(
        f"/projects/{project.b64id}/stories/{NOT_EXISTING_REF}/attachments/{NOT_EXISTING_B64ID}"
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND, response.text


async def test_delete_story_attachments_404_not_found_nonexistent_attachment(client):
    project = await f.create_project()
    story = await f.create_story(project=project)

    client.login(project.created_by)
    response = client.delete(
        f"/projects/{project.b64id}/stories/{story.ref}/attachments/{NOT_EXISTING_B64ID}"
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND, response.text


##########################################################
# GET projects/<id>/stories/<ref>/attachments/<id>/file/<filename>
##########################################################


async def test_get_story_attachment_file_200_ok(client):
    project = await f.create_project()
    story = await f.create_story(project=project)
    user = project.created_by
    attachment = await f.create_attachment(content_object=story, created_by=user)

    client.login(user)
    response = client.get(
        f"/projects/{project.b64id}/stories/{story.ref}/attachments/{attachment.b64id}/file/{attachment.name}"
    )
    assert response.status_code == status.HTTP_200_OK, response.text


async def test_get_story_attachment_file_404_not_found_project(client):
    project = await f.create_project()
    story = await f.create_story(project=project)
    user = project.created_by
    attachment = await f.create_attachment(content_object=story, created_by=user)

    client.login(user)
    response = client.get(
        f"/projects/{NOT_EXISTING_B64ID}/stories/{story.ref}/attachments/{attachment.b64id}/file/{attachment.name}"
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND, response.text


async def test_get_story_attachment_file_404_not_found_story(client):
    project = await f.create_project()
    story = await f.create_story(project=project)
    user = project.created_by
    attachment = await f.create_attachment(content_object=story, created_by=user)

    client.login(user)
    response = client.get(
        f"/projects/{project.b64id}/stories/{NOT_EXISTING_REF}/attachments/{attachment.b64id}/file/{attachment.name}"
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND, response.text


async def test_get_story_attachment_file_404_not_found_attachment(client):
    project = await f.create_project()
    story = await f.create_story(project=project)
    user = project.created_by
    attachment = await f.create_attachment(content_object=story, created_by=user)

    client.login(user)
    response = client.get(
        f"/projects/{project.b64id}/stories/{story.ref}/attachments/{NOT_EXISTING_B64ID}/file/{attachment.name}"
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND, response.text
