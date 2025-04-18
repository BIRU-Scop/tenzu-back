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

from permissions.choices import ProjectPermissions
from tests.utils import factories as f
from tests.utils.bad_params import INVALID_B64ID, NOT_EXISTING_B64ID

pytestmark = pytest.mark.django_db


##########################################################
# POST /projects
##########################################################


async def test_create_project_200_ok_being_workspace_member(client):
    workspace = await f.create_workspace()
    data = {"name": "Project test", "color": 1}
    files = {"logo": ("logo.png", f.build_image_file("logo"), "image/png")}

    client.login(workspace.created_by)
    response = await client.post(
        f"/workspaces/{workspace.b64id}/projects", data=data, files=files
    )
    assert response.status_code == 200, response.data
    res = response.json()
    assert res["userRole"]["isOwner"] is True
    assert res["userIsInvited"] is False
    assert len(res["workflows"]) > 0


async def test_create_project_400_bad_request_invalid_workspace_error(client):
    workspace = await f.create_workspace()
    data = {"name": "My pro#%&乕شject", "color": 1}

    client.login(workspace.created_by)
    response = await client.post(
        f"/workspaces/{NOT_EXISTING_B64ID}/projects", data=data
    )
    assert response.status_code == 404, response.data


async def test_create_project_403_being_no_workspace_member(client):
    workspace = await f.create_workspace()
    user2 = await f.create_user()
    data = {"name": "Project test", "color": 1}
    files = {"logo": ("logo.png", f.build_image_file("logo"), "image/png")}

    client.login(user2)
    response = await client.post(
        f"/workspaces/{workspace.b64id}/projects", data=data, files=files
    )
    assert response.status_code == 403, response.data


async def test_create_project_401_being_anonymous(client):
    workspace = await f.create_workspace()
    data = {"name": "Project test", "color": 1}
    files = {"logo": ("logo.png", f.build_image_file("logo"), "image/png")}

    response = await client.post(
        f"/workspaces/{workspace.b64id}/projects", data=data, files=files
    )
    assert response.status_code == 401, response.data


async def test_create_project_422_unprocessable_color(client):
    workspace = await f.create_workspace()
    data = {"name": "My project", "color": 12}

    client.login(workspace.created_by)
    response = await client.post(f"/workspaces/{workspace.b64id}/projects", data=data)
    assert response.status_code == 422, response.data


async def test_create_project_422_unprocessable_uuid(client):
    workspace = await f.create_workspace()
    data = {"name": "My project", "color": 12}

    client.login(workspace.created_by)
    response = await client.post(f"/workspaces/{INVALID_B64ID}/projects", data=data)
    assert response.status_code == 422, response.data


##########################################################
# GET /workspaces/<id>/projects
##########################################################


async def test_list_workspace_projects_200_ok_owner_no_project(client):
    workspace = await f.create_workspace()
    client.login(workspace.created_by)
    response = await client.get(f"/workspaces/{workspace.b64id}/projects")
    assert response.status_code == 200, response.text
    res = response.json()
    assert res.keys() == {"userMemberProjects", "userInvitedProjects"}
    assert res["userMemberProjects"] == []
    assert res["userInvitedProjects"] == []


async def test_list_workspace_projects_200_ok_owner_one_project(
    client, project_template
):
    workspace = await f.create_workspace()
    project = await f.create_project(template=project_template, workspace=workspace)

    client.login(workspace.created_by)
    response = await client.get(f"/workspaces/{workspace.b64id}/projects")
    assert response.status_code == 200, response.text
    res = response.json()
    assert res.keys() == {"userMemberProjects", "userInvitedProjects"}
    assert len(res["userMemberProjects"]) == 1
    assert res["userMemberProjects"][0]["name"] == project.name
    assert res["userInvitedProjects"] == []


async def test_list_workspace_projects_200_ok_invitee(client, project_template):
    pj_invitation = await f.create_project_invitation()

    client.login(pj_invitation.user)
    response = await client.get(
        f"/workspaces/{pj_invitation.project.workspace.b64id}/projects"
    )
    assert response.status_code == 200, response.data
    res = response.json()
    assert res.keys() == {"userMemberProjects", "userInvitedProjects"}
    assert res["userMemberProjects"] == []
    assert len(res["userInvitedProjects"]) == 1
    assert res["userInvitedProjects"][0]["name"] == pj_invitation.project.name


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
# GET /projects/<id>
##########################################################


async def test_get_project_200_ok_being_project_owner(client, project_template):
    project = await f.create_project(project_template)

    client.login(project.created_by)
    response = await client.get(f"/projects/{project.b64id}")
    assert response.status_code == 200, response.data
    res = response.json()
    assert res["userRole"]["isOwner"] is True
    assert res["userIsInvited"] is False
    assert len(res["workflows"]) > 0


async def test_get_project_200_ok_being_project_member_without_view_workflows(
    client, project_template
):
    project = await f.create_project(project_template)
    general_member_role = await f.create_project_role(
        permissions=[],
        is_owner=False,
        project=project,
    )

    user = await f.create_user()
    await f.create_project_membership(
        user=user, project=project, role=general_member_role
    )

    client.login(user)
    response = await client.get(f"/projects/{project.b64id}")
    assert response.status_code == 200, response.data
    res = response.json()
    assert res["userRole"]["isOwner"] is False
    assert res["userIsInvited"] is False
    assert res["workflows"] == []


async def test_get_project_200_ok_being_project_member(client, project_template):
    project = await f.create_project(project_template)
    general_member_role = await f.create_project_role(
        permissions=[ProjectPermissions.VIEW_WORKFLOW.value],
        is_owner=False,
        project=project,
    )

    pj_member = await f.create_user()
    await f.create_project_membership(
        user=pj_member, project=project, role=general_member_role
    )

    client.login(pj_member)
    response = await client.get(f"/projects/{project.b64id}")
    assert response.status_code == 200, response.data
    res = response.json()
    assert res["userRole"]["isOwner"] is False
    assert res["userIsInvited"] is False
    assert len(res["workflows"]) > 0


async def test_get_project_200_ok_being_invited_user(client, project_template):
    project = await f.create_project(project_template)
    general_member_role = await f.create_project_role(
        is_owner=False,
        project=project,
    )

    user = await f.create_user()
    await f.create_project_invitation(
        user=user, project=project, role=general_member_role
    )

    client.login(user)
    response = await client.get(f"/projects/{project.b64id}")
    assert response.status_code == 200, response.data
    res = response.json()
    assert res["userRole"] is None
    assert res["userIsInvited"] is True
    assert res["workflows"] == []


async def test_get_project_403_forbidden_not_project_member(client, project_template):
    project = await f.create_project(project_template)
    user = await f.create_user()

    client.login(user)
    response = await client.get(f"/projects/{project.b64id}")
    assert response.status_code == 403, response.data


async def test_get_project_401_forbidden_being_anonymous(client, project_template):
    project = await f.create_project(project_template)

    response = await client.get(f"/projects/{project.b64id}")
    assert response.status_code == 401, response.data


async def test_get_project_404_not_found_project_b64id(
    client,
):
    user = await f.create_user()
    client.login(user)
    response = await client.get(f"/projects/{NOT_EXISTING_B64ID}")
    assert response.status_code == 404, response.data


async def test_get_project_422_unprocessable_project_b64id(
    client,
):
    user = await f.create_user()
    client.login(user)
    response = await client.get(f"/projects/{INVALID_B64ID}")
    assert response.status_code == 422, response.data


##########################################################
# PATCH /projects/<id>/
##########################################################


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
    assert response.status_code == 200, response.data
    updated_project = response.json()
    assert updated_project["name"] == "New name"
    assert updated_project["description"] == "new description"
    assert "new-logo.png" in updated_project["logo"]
    assert updated_project["userRole"]["isOwner"] is True
    assert updated_project["userIsInvited"] is False
    assert len(updated_project["workflows"]) > 0


async def test_update_project_files_200_ok_no_logo_change(client, project_template):
    image = f.build_image_file("new-logo")
    project = await f.create_project(project_template, logo=image)

    data = {"name": "New name", "description": "new description"}

    client.login(project.created_by)
    response = await client.post(
        f"/projects/{project.b64id}",
        data=data,
        FILES={},
    )
    assert response.status_code == 200, response.data
    updated_project = response.json()
    assert updated_project["name"] == "New name"
    assert updated_project["description"] == "new description"
    assert "new-logo.png" in updated_project["logo"]


async def test_update_project_files_200_ok_delete_logo(client, project_template):
    image = f.build_image_file("new-logo")
    project = await f.create_project(project_template, logo=image)

    data = {"name": "New name", "description": "new description"}

    client.login(project.created_by)
    response = await client.post(
        f"/projects/{project.b64id}",
        data=data,
        FILES={"logo": None},
    )
    assert response.status_code == 200, response.data
    updated_project = response.json()
    assert updated_project["name"] == "New name"
    assert updated_project["description"] == "new description"
    assert not updated_project["logo"]


async def test_update_project_200_ok_delete_description(client, project_template):
    project = await f.create_project(project_template)

    data = {"description": ""}

    client.login(project.created_by)
    response = await client.post(f"/projects/{project.b64id}", data=data)
    assert response.status_code == 200, response.data
    updated_project = response.json()
    assert updated_project["name"] == project.name
    assert updated_project["description"] == ""


async def test_update_project_422_empty_name(client, project_template):
    project = await f.create_project(project_template)

    data = {"name": ""}

    client.login(project.created_by)
    response = await client.post(f"/projects/{project.b64id}", data=data)
    assert response.status_code == 422, response.data

    data = {"name": None}

    client.login(project.created_by)
    response = await client.post(f"/projects/{project.b64id}", data=data)
    assert response.status_code == 200, response.data
    assert response.json()["name"] == project.name


async def test_update_project_200_ok_member(client, project_template):
    project = await f.create_project(project_template)
    general_member_role = await f.create_project_role(
        permissions=[ProjectPermissions.MODIFY_PROJECT.value],
        is_owner=False,
        project=project,
    )

    user = await f.create_user()
    await f.create_project_membership(
        user=user, project=project, role=general_member_role
    )

    data = {"name": "new name"}

    client.login(user)
    response = await client.post(f"/projects/{project.b64id}", data=data)
    assert response.status_code == 200, response.data
    updated_project = response.json()
    assert updated_project["userRole"]["isOwner"] is False
    assert updated_project["userIsInvited"] is False
    assert updated_project["workflows"] == []


async def test_update_project_403_forbidden_member_without_permissions(
    client, project_template
):
    project = await f.create_project(project_template)
    general_member_role = await f.create_project_role(
        permissions=[],
        is_owner=False,
        project=project,
    )

    user = await f.create_user()
    await f.create_project_membership(
        user=user, project=project, role=general_member_role
    )

    data = {"name": "new name"}
    client.login(user)
    response = await client.post(f"/projects/{project.b64id}", data=data)
    assert response.status_code == 403, response.data


async def test_update_project_403_forbidden_not_member(client, project_template):
    other_user = await f.create_user()
    project = await f.create_project(project_template)

    data = {"name": "new name"}
    client.login(other_user)
    response = await client.post(f"/projects/{project.b64id}", data=data)
    assert response.status_code == 403, response.data


async def test_update_project_404_not_found_project_b64id(
    client,
):
    user = await f.create_user()
    data = {"name": "new name"}

    client.login(user)
    response = await client.post(f"/projects/{NOT_EXISTING_B64ID}", data=data)
    assert response.status_code == 404, response.data


async def test_update_project_422_unprocessable_project_b64id(client):
    user = await f.create_user()
    data = {"name": "new name"}

    client.login(user)
    response = await client.post(f"/projects/{INVALID_B64ID}", data=data)
    assert response.status_code == 422, response.data


##########################################################
# DELETE /projects/<id>
##########################################################


async def test_delete_project_204_no_content_being_proj_owner(client, project_template):
    project = await f.create_project(project_template)

    client.login(project.created_by)
    response = await client.delete(f"/projects/{project.b64id}")
    assert response.status_code == 204, response.data


async def test_delete_project_204_no_content_being_proj_member(
    client, project_template
):
    project = await f.create_project(project_template)
    general_member_role = await f.create_project_role(
        permissions=[ProjectPermissions.DELETE_PROJECT.value],
        is_owner=False,
        project=project,
    )

    user = await f.create_user()
    await f.create_project_membership(
        user=user, project=project, role=general_member_role
    )
    client.login(user)
    response = await client.delete(f"/projects/{project.b64id}")
    assert response.status_code == 204, response.data


async def test_delete_project_403_forbidden_member_without_permissions(
    client, project_template
):
    project = await f.create_project(project_template)
    general_member_role = await f.create_project_role(
        permissions=[],
        is_owner=False,
        project=project,
    )

    user = await f.create_user()
    await f.create_project_membership(
        user=user, project=project, role=general_member_role
    )

    client.login(user)
    response = await client.delete(f"/projects/{project.b64id}")
    assert response.status_code == 403, response.data


async def test_delete_project_403_forbidden_not_member(client, project_template):
    project = await f.create_project(project_template)
    user = await f.create_user()

    client.login(user)
    response = await client.delete(f"/projects/{project.b64id}")
    assert response.status_code == 403, response.data


async def test_delete_project_404_not_found_project_b64id(client):
    pj_owner = await f.create_user()
    client.login(pj_owner)
    response = await client.delete(f"/projects/{NOT_EXISTING_B64ID}")
    assert response.status_code == 404, response.data


async def test_delete_project_422_unprocessable_project_b64id(client):
    pj_owner = await f.create_user()
    client.login(pj_owner)
    response = await client.delete(f"/projects/{INVALID_B64ID}")
    assert response.status_code == 422, response.data
