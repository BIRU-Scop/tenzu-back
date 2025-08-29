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
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from permissions.choices import ProjectPermissions
from tests.utils import factories as f
from tests.utils.bad_params import (
    INVALID_B64ID,
    NOT_EXISTING_B64ID,
    NOT_EXISTING_REF,
)

pytestmark = pytest.mark.django_db


##########################################################
# POST /projects/<b64id>/stories/<ref>/stories/attachments
##########################################################


async def test_create_story_attachment_200_ok(client, project_template):
    project = await f.create_project(project_template)
    story = await f.create_story(project=project)
    files = {"file": SimpleUploadedFile("test.txt", b"data345")}

    client.login(project.created_by)
    response = await client.post(
        f"/projects/{project.b64id}/stories/{story.ref}/attachments",
        FILES=files,
    )
    assert response.status_code == 200, response.data["data"]

    user = await f.create_user()
    general_member_role = await f.create_project_role(
        permissions=[ProjectPermissions.MODIFY_STORY.value],
        is_owner=False,
        project=project,
    )
    await f.create_project_membership(
        user=user, project=project, role=general_member_role
    )

    client.login(user)
    response = await client.post(
        f"/projects/{project.b64id}/stories/{story.ref}/attachments",
        FILES=files,
    )
    assert response.status_code == 200, response.data["data"]


async def test_create_story_attachment_401_forbidden_anonymous(
    client, project_template
):
    project = await f.create_project(project_template)
    story = await f.create_story(project=project)
    files = {"file": SimpleUploadedFile("test.txt", b"data345")}

    response = await client.post(
        f"/projects/{project.b64id}/stories/{story.ref}/attachments",
        FILES=files,
    )
    assert response.status_code == 401, response.data


async def test_create_story_attachment_403_forbidden_error_not_member(
    client, project_template
):
    project = await f.create_project(project_template)
    story = await f.create_story(project=project)
    user = await f.create_user()
    files = {"file": SimpleUploadedFile("test.txt", b"data345")}

    client.login(user)
    response = await client.post(
        f"/projects/{project.b64id}/stories/{story.ref}/attachments",
        FILES=files,
    )
    assert response.status_code == 403, response.data


async def test_create_story_attachment_403_forbidden_error_no_permissions(
    client, project_template
):
    project = await f.create_project(project_template)
    story = await f.create_story(project=project)
    user = await f.create_user()
    general_member_role = await f.create_project_role(
        permissions=[],
        is_owner=False,
        project=project,
    )
    await f.create_project_membership(
        user=user, project=project, role=general_member_role
    )
    files = {"file": SimpleUploadedFile("test.txt", b"data345")}

    client.login(user)
    response = await client.post(
        f"/projects/{project.b64id}/stories/{story.ref}/attachments",
        FILES=files,
    )
    assert response.status_code == 403, response.data


async def test_create_story_attachment_404_not_found_project_b64id(
    client, project_template
):
    project = await f.create_project(project_template)
    story = await f.create_story(project=project)
    user = project.created_by
    files = {"file": SimpleUploadedFile("test.txt", b"data345")}

    client.login(user)
    response = await client.post(
        f"/projects/{NOT_EXISTING_B64ID}/stories/{story.ref}/attachments",
        FILES=files,
    )
    assert response.status_code == 404, response.data


async def test_create_story_attachment_404_not_found_story_ref(
    client, project_template
):
    project = await f.create_project(project_template)
    user = project.created_by
    files = {"file": SimpleUploadedFile("test.txt", b"data345")}

    client.login(user)
    response = await client.post(
        f"/projects/{project.b64id}/stories/{NOT_EXISTING_REF}/attachments",
        FILES=files,
    )
    assert response.status_code == 404, response.data


async def test_create_story_attachment_422_unprocessable_entity_project_b64id(
    client, project_template
):
    project = await f.create_project(project_template)
    story = await f.create_story(project=project)
    user = project.created_by
    files = {"file": SimpleUploadedFile("test.txt", b"data345")}

    client.login(user)
    response = await client.post(
        f"/projects/{INVALID_B64ID}/stories/{story.ref}/attachments",
        FILES=files,
    )
    assert response.status_code == 422, response.data


async def test_create_story_attachment_422_unprocessable_entity_bad_request(
    client, project_template
):
    project = await f.create_project(project_template)
    story = await f.create_story(project=project)
    user = project.created_by

    client.login(user)
    response = await client.post(
        f"/projects/{project.b64id}/stories/{story.ref}/attachments",
    )
    assert response.status_code == 422, response.data


async def test_create_story_attachment_422_too_big(client, project_template):
    project = await f.create_project(project_template)
    story = await f.create_story(project=project)
    files = {
        "file": SimpleUploadedFile(
            "test.txt", b"a" * (settings.MAX_UPLOAD_FILE_SIZE + 1)
        )
    }

    client.login(project.created_by)
    response = await client.post(
        f"/projects/{project.b64id}/stories/{story.ref}/attachments",
        FILES=files,
    )
    assert response.status_code == 422, response.data


##########################################################
# GET projects/<id>/stories/<ref>/attachments
##########################################################


async def test_list_story_attachments_200_ok(client, project_template):
    project = await f.create_project(project_template)
    story = await f.create_story(project=project)
    user = project.created_by
    await f.create_attachment(content_object=story, created_by=user)
    await f.create_attachment(content_object=story, created_by=user)

    client.login(user)
    response = await client.get(
        f"/projects/{project.b64id}/stories/{story.ref}/attachments"
    )
    assert response.status_code == 200, response.data["data"]
    res = response.data["data"]
    assert len(res) == 2

    user = await f.create_user()
    general_member_role = await f.create_project_role(
        permissions=[ProjectPermissions.VIEW_STORY.value],
        is_owner=False,
        project=project,
    )
    await f.create_project_membership(
        user=user, project=project, role=general_member_role
    )
    client.login(user)
    response = await client.get(
        f"/projects/{project.b64id}/stories/{story.ref}/attachments"
    )
    assert response.status_code == 200, response.data["data"]
    res = response.data["data"]
    assert len(res) == 2


async def test_list_story_attachments_401_forbidden_anonymous(client, project_template):
    project = await f.create_project(project_template)
    story = await f.create_story(project=project)

    response = await client.get(
        f"/projects/{project.b64id}/stories/{story.ref}/attachments"
    )
    assert response.status_code == 401, response.data


async def test_list_story_attachments_403_forbidden_not_member(
    client, project_template
):
    user = await f.create_user()
    project = await f.create_project(project_template)
    story = await f.create_story(project=project)

    client.login(user)
    response = await client.get(
        f"/projects/{project.b64id}/stories/{story.ref}/attachments"
    )
    assert response.status_code == 403, response.data


async def test_list_story_attachments_403_forbidden_no_permissions(
    client, project_template
):
    user = await f.create_user()
    project = await f.create_project(project_template)
    story = await f.create_story(project=project)
    general_member_role = await f.create_project_role(
        permissions=[],
        is_owner=False,
        project=project,
    )
    await f.create_project_membership(
        user=user, project=project, role=general_member_role
    )

    client.login(user)
    response = await client.get(
        f"/projects/{project.b64id}/stories/{story.ref}/attachments"
    )
    assert response.status_code == 403, response.data


async def test_list_story_attachments_404_not_found_project(client):
    user = await f.create_user()

    client.login(user)
    response = await client.get(f"/projects/{NOT_EXISTING_B64ID}/stories/1/attachments")
    assert response.status_code == 404, response.data


async def test_list_story_attachments_404_not_found_story(client, project_template):
    project = await f.create_project(project_template)
    user = project.created_by

    client.login(user)
    response = await client.get(
        f"/projects/{project.b64id}/stories/{NOT_EXISTING_REF}/attachments"
    )
    assert response.status_code == 404, response.data


##########################################################
# DELETE stories/attachments/<id>
##########################################################


async def test_delete_story_attachment_204_no_content(client, project_template):
    project = await f.create_project(project_template)
    user = project.created_by
    story = await f.create_story(project=project)
    attachment = await f.create_attachment(content_object=story, created_by=user)

    client.login(user)
    response = await client.delete(f"/stories/attachments/{attachment.b64id}")
    assert response.status_code == 204, response.data

    attachment = await f.create_attachment(content_object=story, created_by=user)
    user = await f.create_user()
    general_member_role = await f.create_project_role(
        permissions=[ProjectPermissions.MODIFY_STORY.value],
        is_owner=False,
        project=project,
    )
    await f.create_project_membership(
        user=user, project=project, role=general_member_role
    )
    client.login(user)
    response = await client.delete(f"/stories/attachments/{attachment.b64id}")
    assert response.status_code == 204, response.data


async def test_delete_story_attachment_401_forbidden_anonymous(
    client, project_template
):
    project = await f.create_project(project_template)
    story = await f.create_story(project=project)
    attachment = await f.create_attachment(
        content_object=story, created_by=project.created_by
    )

    response = await client.delete(f"/stories/attachments/{attachment.b64id}")
    assert response.status_code == 401, response.data


async def test_delete_story_attachment_403_forbidden_not_member(
    client, project_template
):
    project = await f.create_project(project_template)
    story = await f.create_story(project=project)
    attachment = await f.create_attachment(
        content_object=story, created_by=project.created_by
    )
    user = await f.create_user()

    client.login(user)
    response = await client.delete(f"/stories/attachments/{attachment.b64id}")
    assert response.status_code == 403, response.data


async def test_delete_story_attachment_403_forbidden_no_permission(
    client, project_template
):
    project = await f.create_project(project_template)
    story = await f.create_story(project=project)
    attachment = await f.create_attachment(
        content_object=story, created_by=project.created_by
    )

    user = await f.create_user()
    general_member_role = await f.create_project_role(
        permissions=[],
        is_owner=False,
        project=project,
    )
    await f.create_project_membership(
        user=user, project=project, role=general_member_role
    )
    client.login(user)
    response = await client.delete(f"/stories/attachments/{attachment.b64id}")
    assert response.status_code == 403, response.data


async def test_delete_story_attachment_404_not_story_attachment(client):
    user = await f.create_user()
    workflow = await f.create_workflow()
    attachment = await f.create_attachment(content_object=workflow, created_by=user)

    client.login(user)
    response = await client.delete(
        f"/stories/attachments/{attachment.b64id}",
    )
    assert response.status_code == 404, response.data


async def test_delete_story_attachment_404_not_found_nonexistent_attachment(client):
    client.login(await f.create_user())
    response = await client.delete(f"/stories/attachments/{NOT_EXISTING_B64ID}")
    assert response.status_code == 404, response.data


##########################################################
# GET stories/attachments/<id>/file/<filename>
##########################################################


async def test_get_story_attachment_file_200_ok(client, project_template):
    project = await f.create_project(project_template)
    story = await f.create_story(project=project)
    user = project.created_by
    attachment = await f.create_attachment(content_object=story, created_by=user)

    client.login(user)
    response = await client.get(f"/stories/attachments/{attachment.b64id}")
    assert response.status_code == 200, response.data["data"]

    user = await f.create_user()
    general_member_role = await f.create_project_role(
        permissions=[ProjectPermissions.VIEW_STORY.value],
        is_owner=False,
        project=project,
    )
    await f.create_project_membership(
        user=user, project=project, role=general_member_role
    )
    client.login(user)
    response = await client.get(f"/stories/attachments/{attachment.b64id}")
    assert response.status_code == 200, response.data["data"]


async def test_get_story_attachment_file_401_forbidden_anonymous(
    client, project_template
):
    project = await f.create_project(project_template)
    story = await f.create_story(project=project)
    attachment = await f.create_attachment(
        content_object=story, created_by=project.created_by
    )

    response = await client.get(f"/stories/attachments/{attachment.b64id}")
    assert response.status_code == 401, response.data


async def test_get_story_attachment_file_403_forbidden_not_member(
    client, project_template
):
    project = await f.create_project(project_template)
    story = await f.create_story(project=project)
    attachment = await f.create_attachment(
        content_object=story, created_by=project.created_by
    )
    user = await f.create_user()

    client.login(user)
    response = await client.get(f"/stories/attachments/{attachment.b64id}")
    assert response.status_code == 403, response.data


async def test_get_story_attachment_file_403_forbidden_no_permission(
    client, project_template
):
    project = await f.create_project(project_template)
    story = await f.create_story(project=project)
    attachment = await f.create_attachment(
        content_object=story, created_by=project.created_by
    )

    user = await f.create_user()
    general_member_role = await f.create_project_role(
        permissions=[],
        is_owner=False,
        project=project,
    )
    await f.create_project_membership(
        user=user, project=project, role=general_member_role
    )
    client.login(user)
    response = await client.get(f"/stories/attachments/{attachment.b64id}")
    assert response.status_code == 403, response.data


async def test_get_story_attachment_file_404_not_story_attachment(client):
    user = await f.create_user()
    workflow = await f.create_workflow()
    attachment = await f.create_attachment(content_object=workflow, created_by=user)

    client.login(user)
    response = await client.get(
        f"/stories/attachments/{attachment.b64id}",
    )
    assert response.status_code == 404, response.data


async def test_get_story_attachment_file_404_not_found_attachment(client):
    client.login(await f.create_user())
    response = await client.get(f"/stories/attachments/{NOT_EXISTING_B64ID}")
    assert response.status_code == 404, response.data
