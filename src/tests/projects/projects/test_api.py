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
from django.core.files.uploadedfile import InMemoryUploadedFile

from permissions import choices
from tests.utils import factories as f
from tests.utils.bad_params import INVALID_B64ID, NOT_EXISTING_B64ID

pytestmark = pytest.mark.django_db(transaction=True)


##########################################################
# POST /projects
##########################################################


async def test_create_project_200_ok_being_workspace_member(client):
    workspace = await f.create_workspace()
    data = {"name": "Project test", "color": 1, "workspaceId": workspace.b64id}
    files = {"logo": ("logo.png", f.build_image_file("logo"), "image/png")}

    client.login(workspace.created_by)
    response = await client.post("/projects", data=data, files=files)
    assert response.status_code == 200, response.text


async def test_create_project_400_bad_request_invalid_workspace_error(client):
    workspace = await f.create_workspace()
    non_existing_uuid = "6JgsbGyoEe2VExhWgGrI2w"
    data = {"name": "My pro#%&乕شject", "color": 1, "workspaceId": non_existing_uuid}

    client.login(workspace.created_by)
    response = await client.post("/projects", data=data)
    assert response.status_code == 400, response.text


async def test_create_project_403_being_no_workspace_member(client):
    workspace = await f.create_workspace()
    user2 = await f.create_user()
    data = {"name": "Project test", "color": 1, "workspaceId": workspace.b64id}
    files = {"logo": ("logo.png", f.build_image_file("logo"), "image/png")}

    client.login(user2)
    response = await client.post("/projects", data=data, files=files)
    assert response.status_code == 403, response.text


async def test_create_project_401_being_anonymous(client):
    workspace = await f.create_workspace()
    data = {"name": "Project test", "color": 1, "workspaceId": workspace.b64id}
    files = {"logo": ("logo.png", f.build_image_file("logo"), "image/png")}

    response = await client.post("/projects", data=data, files=files)
    assert response.status_code == 401, response.text


async def test_create_project_422_unprocessable_color(client):
    workspace = await f.create_workspace()
    data = {"name": "My project", "color": 12, "workspaceId": workspace.b64id}

    client.login(workspace.created_by)
    response = await client.post("/projects", data=data)
    assert response.status_code == 422, response.text


##########################################################
# GET /workspaces/<id>/projects
##########################################################


async def test_list_workspace_projects_200_ok(client, project_template):
    workspace = await f.create_workspace()
    await f.create_project(
        template=project_template, workspace=workspace, created_by=workspace.created_by
    )

    client.login(workspace.created_by)
    response = await client.get(f"/workspaces/{workspace.b64id}/projects")
    assert response.status_code == 200, response.text
    assert len(response.json()) == 1


async def test_list_workspace_projects_404_not_found_workspace_b64id(client):
    user = await f.create_user()
    client.login(user)
    response = await client.get(f"/workspaces/{NOT_EXISTING_B64ID}/projects")
    assert response.status_code == 404, response.text


async def test_list_workspace_projects_422_unprocessable_workspace_b64id(client):
    user = await f.create_user()
    client.login(user)
    response = await client.get(f"/workspaces/{INVALID_B64ID}/projects")
    assert response.status_code == 422, response.text


##########################################################
# GET /workspaces/<id>/invited-projects
##########################################################


async def test_list_workspace_invited_projects_200_ok(client, project_template):
    workspace = await f.create_workspace()
    project = await f.create_project(
        template=project_template, workspace=workspace, created_by=workspace.created_by
    )
    user2 = await f.create_user()
    await f.create_workspace_membership(user=user2, workspace=workspace)
    await f.create_project_invitation(
        email=user2.email, user=user2, project=project, invited_by=workspace.created_by
    )

    client.login(user2)
    response = await client.get(f"/workspaces/{workspace.b64id}/invited-projects")
    assert response.status_code == 200, response.text
    assert len(response.json()) == 1


async def test_list_workspace_invited_projects_404_not_found_workspace_b64id(client):
    user = await f.create_user()
    client.login(user)
    response = await client.get(f"/workspaces/{NOT_EXISTING_B64ID}/invited-projects")
    assert response.status_code == 404, response.text


async def test_list_workspace_invited_projects_422_unproccessable_workspace_b64id(
    client,
):
    user = await f.create_user()
    client.login(user)
    response = await client.get(f"/workspaces/{INVALID_B64ID}/invited-projects")
    assert response.status_code == 422, response.text


##########################################################
# GET /projects/<id>
##########################################################


async def test_get_project_200_ok_being_project_admin(client, project_template):
    project = await f.create_project(project_template)

    client.login(project.created_by)
    response = await client.get(f"/projects/{project.b64id}")
    assert response.status_code == 200, response.text


async def test_get_project_200_ok_being_project_member(client, project_template):
    project = await f.create_project(project_template)
    general_member_role = await f.create_project_role(
        permissions=choices.ProjectPermissions.values,
        is_admin=False,
        project=project,
    )

    user2 = await f.create_user()
    await f.create_project_membership(
        user=user2, project=project, role=general_member_role
    )

    client.login(user2)
    response = await client.get(f"/projects/{project.b64id}")
    assert response.status_code == 200, response.text


async def test_get_project_200_ok_being_invited_user(client, project_template):
    project = await f.create_project(project_template)
    general_member_role = await f.create_project_role(
        permissions=choices.ProjectPermissions.values,
        is_admin=False,
        project=project,
    )

    user2 = await f.create_user()
    await f.create_project_invitation(
        user=user2, project=project, role=general_member_role
    )

    client.login(user2)
    response = await client.get(f"/projects/{project.b64id}")
    assert response.status_code == 200, response.text


async def test_get_project_403_forbidden_not_project_member(client, project_template):
    project = await f.create_project(project_template)
    user2 = await f.create_user()

    client.login(user2)
    response = await client.get(f"/projects/{project.b64id}")
    assert response.status_code == 403, response.text


async def test_get_project_401_forbidden_being_anonymous(client, project_template):
    project = await f.create_project(project_template)

    response = await client.get(f"/projects/{project.b64id}")
    assert response.status_code == 401, response.text


async def test_get_project_404_not_found_project_b64id(
    client,
):
    user = await f.create_user()
    client.login(user)
    response = await client.get(f"/projects/{NOT_EXISTING_B64ID}")
    assert response.status_code == 404, response.text


async def test_get_project_422_unprocessable_project_b64id(
    client,
):
    user = await f.create_user()
    client.login(user)
    response = await client.get(f"/projects/{INVALID_B64ID}")
    assert response.status_code == 422, response.text


##########################################################
# GET /projects/<id>/public-permissions
##########################################################


async def test_get_project_public_permissions_200_ok(client, project_template):
    project = await f.create_project(project_template)

    client.login(project.created_by)
    response = await client.get(f"/projects/{project.b64id}/public-permissions")
    assert response.status_code == 200, response.text


async def test_get_project_public_permissions_403_forbidden_no_admin(
    client, project_template
):
    project = await f.create_project(project_template)
    user2 = await f.create_user()

    client.login(user2)
    response = await client.get(f"/projects/{project.b64id}/public-permissions")
    assert response.status_code == 403, response.text


async def test_get_project_public_permissions_403_forbidden_no_member(
    client, project_template
):
    project = await f.create_project(project_template)
    user = await f.create_user()

    client.login(user)
    response = await client.get(f"/projects/{project.b64id}/public-permissions")
    assert response.status_code == 403, response.text


async def test_get_project_public_permissions_401_forbidden_anonymous_user(
    client, project_template
):
    project = await f.create_project(project_template)

    response = await client.get(f"/projects/{project.b64id}/public-permissions")
    assert response.status_code == 401, response.text


async def test_get_project_public_permissions_404_not_found_project_b64id(
    client, project_template
):
    user = await f.create_user()
    client.login(user)
    response = await client.get(f"/projects/{NOT_EXISTING_B64ID}")
    assert response.status_code == 404, response.text


async def test_get_project_public_permissions_422_unprocessable_project_b64id(
    client, project_template
):
    user = await f.create_user()
    client.login(user)
    response = await client.get(f"/projects/{INVALID_B64ID}")
    assert response.status_code == 422, response.text


##########################################################
# PATCH /projects/<id>/
##########################################################


async def test_update_project_200_ok(client, project_template):
    project = await f.create_project(project_template)
    image = f.build_image_file("new-logo")

    logo = InMemoryUploadedFile(
        image, None, "new-logo.png", "image/png", image.size, None, None
    )
    data = {"name": "New name", "description": "new description", "logo": logo}

    client.login(project.created_by)
    response = await client.post(
        f"/projects/{project.b64id}",
        data=data,
    )
    assert response.status_code == 200, response.text
    updated_project = response.json()
    assert updated_project["name"] == "New name"
    assert updated_project["description"] == "new description"
    assert "new-logo.png" in updated_project["logo"]


async def test_update_project_files_200_ok(client, project_template):
    project = await f.create_project(project_template)
    image = f.build_image_file("new-logo")

    logo = InMemoryUploadedFile(
        image, None, "new-logo.png", "image/png", image.size, None, None
    )
    data = {"name": "New name", "description": "new description"}

    client.login(project.created_by)
    response = await client.post(
        f"/projects/{project.b64id}",
        data=data,
        FILES={"logo": logo},
    )
    assert response.status_code == 200, response.text
    updated_project = response.json()
    assert updated_project["name"] == "New name"
    assert updated_project["description"] == "new description"
    assert "new-logo.png" in updated_project["logo"]


async def test_update_project_200_ok_delete_description(client, project_template):
    project = await f.create_project(project_template)

    data = {"description": ""}

    client.login(project.created_by)
    response = await client.post(f"/projects/{project.b64id}", data=data)
    assert response.status_code == 200, response.text
    updated_project = response.json()
    assert updated_project["name"] == project.name
    assert updated_project["description"] == ""


async def test_update_project_403_forbidden_no_admin(client, project_template):
    other_user = await f.create_user()
    project = await f.create_project(project_template)

    data = {"name": "new name"}
    client.login(other_user)
    response = await client.post(f"/projects/{project.b64id}", data=data)
    assert response.status_code == 403, response.text


async def test_update_project_404_not_found_project_b64id(
    client,
):
    user = await f.create_user()
    data = {"name": "new name"}

    client.login(user)
    response = await client.post(f"/projects/{NOT_EXISTING_B64ID}", data=data)
    assert response.status_code == 404, response.text


async def test_update_project_422_unprocessable_project_b64id(client):
    user = await f.create_user()
    data = {"name": "new name"}

    client.login(user)
    response = await client.post(f"/projects/{INVALID_B64ID}", data=data)
    assert response.status_code == 422, response.text


##########################################################
# PUT /projects/<id>/public-permissions
##########################################################


@pytest.mark.parametrize(
    "permissions",
    [
        (["view_story"]),
        (["view_story", "modify_story"]),
    ],
)
async def test_update_project_public_permissions_200_ok(
    client, permissions, project_template
):
    project = await f.create_project(project_template)
    data = {"permissions": permissions}

    client.login(project.created_by)
    response = await client.put(
        f"/projects/{project.b64id}/public-permissions", json=data
    )
    assert response.status_code == 200, response.text


async def test_update_project_public_permissions_403_forbidden_no_admin(
    client, project_template
):
    project = await f.create_project(project_template)
    user2 = await f.create_user()
    data = {"permissions": []}

    client.login(user2)
    response = await client.put(
        f"/projects/{project.b64id}/public-permissions", json=data
    )
    assert response.status_code == 403, response.text


async def test_update_project_public_permissions_403_forbidden_no_member(
    client, project_template
):
    project = await f.create_project(project_template)
    user = await f.create_user()
    data = {"permissions": []}

    client.login(user)
    response = await client.put(
        f"/projects/{project.b64id}/public-permissions", json=data
    )
    assert response.status_code == 403, response.text


async def test_update_project_public_permissions_401_forbidden_anonymous_user(
    client, project_template
):
    project = await f.create_project(project_template)
    data = {"permissions": []}

    response = await client.put(
        f"/projects/{project.b64id}/public-permissions", json=data
    )
    assert response.status_code == 401, response.text


async def test_update_project_public_permissions_404_not_found_project_b64id(client):
    user = await f.create_user()
    data = {"permissions": ["view_story"]}

    client.login(user)
    response = await client.put(
        f"/projects/{NOT_EXISTING_B64ID}/public-permissions", json=data
    )
    assert response.status_code == 404, response.text


@pytest.mark.parametrize(
    "permissions",
    [
        (["modify_story"]),
        (["delete_story"]),
    ],
)
async def test_update_project_public_permissions_422_unprocessable_incompatible(
    client, permissions, project_template
):
    project = await f.create_project(project_template)
    data = {"permissions": permissions}

    client.login(project.created_by)
    response = await client.put(
        f"/projects/{project.b64id}/public-permissions", json=data
    )
    assert response.status_code == 422, response.text


async def test_update_project_public_permissions_422_unprocessable_not_valid(
    client, project_template
):
    project = await f.create_project(project_template)
    data = {"permissions": ["not_valid"]}

    client.login(project.created_by)
    response = await client.put(
        f"/projects/{project.b64id}/public-permissions", json=data
    )
    assert response.status_code == 422, response.text


async def test_update_project_public_permissions_422_unprocessable_project_b64id(
    client,
):
    user = await f.create_user()
    data = {"permissions": []}

    client.login(user)
    response = await client.put(
        f"/projects/{INVALID_B64ID}/public-permissions", json=data
    )
    assert response.status_code == 422, response.text


##########################################################
# DELETE /projects/<id>
##########################################################


async def test_delete_project_204_no_content_being_proj_admin(client, project_template):
    project = await f.create_project(project_template)

    client.login(project.created_by)
    response = await client.delete(f"/projects/{project.b64id}")
    assert response.status_code == 204, response.text


async def test_delete_project_204_no_content_being_ws_admin(client, project_template):
    ws = await f.create_workspace()
    project = await f.create_project(template=project_template, workspace=ws)

    client.login(ws.created_by)
    response = await client.delete(f"/projects/{project.b64id}")
    assert response.status_code == 204, response.text


async def test_delete_project_403_forbidden_user_without_permissions(
    client, project_template
):
    project = await f.create_project(project_template)
    user = await f.create_user()

    client.login(user)
    response = await client.delete(f"/projects/{project.b64id}")
    assert response.status_code == 403, response.text


async def test_delete_project_404_not_found_project_b64id(client):
    pj_admin = await f.create_user()
    client.login(pj_admin)
    response = await client.delete(f"/projects/{NOT_EXISTING_B64ID}")
    assert response.status_code == 404, response.text


async def test_delete_project_422_unprocessable_project_b64id(client):
    pj_admin = await f.create_user()
    client.login(pj_admin)
    response = await client.delete(f"/projects/{INVALID_B64ID}")
    assert response.status_code == 422, response.text


##########################################################
# GET /my/projects/<id>/permissions
##########################################################


async def test_get_my_project_permissions_200_ok(client, project_template):
    project = await f.create_project(project_template)

    client.login(project.created_by)
    response = await client.get(f"/my/projects/{project.b64id}/permissions")
    assert response.status_code == 200, response.text


async def test_get_my_project_permissions_404_not_found_project_b64id(client):
    user = await f.create_user()

    client.login(user)
    response = await client.get(f"/my/projects/{NOT_EXISTING_B64ID}/permissions")
    assert response.status_code == 404, response.text


async def test_get_my_project_permissions_422_unprocessable_project_b64id(client):
    user = await f.create_user()

    client.login(user)
    response = await client.get(f"/my/projects/{INVALID_B64ID}/permissions")
    assert response.status_code == 422, response.text
