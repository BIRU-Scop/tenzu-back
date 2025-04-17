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

import uuid

import pytest

from memberships.choices import InvitationStatus
from tests.utils import factories as f
from workspaces.workspaces import repositories
from workspaces.workspaces.models import Workspace

pytestmark = pytest.mark.django_db

##########################################################
# create_workspace
##########################################################


async def test_create_workspace_with_non_ASCI_chars():
    user = await f.create_user()
    workspace = await repositories.create_workspace(
        name="My w0r#%&乕شspace", color=3, created_by=user
    )
    assert workspace.name == "My w0r#%&乕شspace"


##########################################################
# list_user_workspaces_overview
##########################################################


async def test_list_user_workspaces_overview_invited_projects(project_template):
    user1 = await f.create_user()
    user2 = await f.create_user()
    user3 = await f.create_user()

    # user1 is owner of several workspaces
    ws1 = await f.create_workspace(name="ws1", created_by=user1)
    ws2 = await f.create_workspace(name="ws2", created_by=user1)
    ws3 = await f.create_workspace(name="ws3", created_by=user1)
    ws4 = await f.create_workspace(name="ws4", created_by=user1)
    ws5 = await f.create_workspace(name="ws5", created_by=user1)

    # user2 is member of ws1
    ws1_member_role = await ws1.roles.aget(slug="member")
    await f.create_workspace_invitation(
        email=user2.email,
        user=user2,
        workspace=ws1,
        role=ws1_member_role,
        invited_by=user1,
        status=InvitationStatus.ACCEPTED,
    )
    await f.create_workspace_membership(user=user2, workspace=ws1, role=ws1_member_role)

    # user2 is member of a project in ws1
    pj1_ws1 = await f.create_project(
        template=project_template, name="pj1_ws1", workspace=ws1, created_by=user1
    )
    pj1_ws1_member_role = await pj1_ws1.roles.aget(slug="admin")
    await f.create_project_invitation(
        email=user2.email,
        user=user2,
        project=pj1_ws1,
        role=pj1_ws1_member_role,
        invited_by=user1,
        status=InvitationStatus.ACCEPTED,
    )
    await f.create_project_membership(
        user=user2, project=pj1_ws1, role=pj1_ws1_member_role
    )
    # user1 invites user3 to a project in ws1 (just email)
    pj2_ws1 = await f.create_project(
        template=project_template, name="pj2_ws1", workspace=ws1, created_by=user1
    )
    pj2_ws1_member_role = await pj2_ws1.roles.aget(slug="member")
    await f.create_project_invitation(
        email=user3.email,
        user=None,
        project=pj2_ws1,
        role=pj2_ws1_member_role,
        invited_by=user1,
    )
    # user1 invites user2 to a project in ws1
    pj3_ws1 = await f.create_project(
        template=project_template, name="pj3_ws1", workspace=ws1, created_by=user1
    )
    pj3_ws1_member_role = await pj3_ws1.roles.aget(slug="member")
    await f.create_project_invitation(
        email=user2.email,
        user=user2,
        project=pj3_ws1,
        role=pj3_ws1_member_role,
        invited_by=user1,
    )
    # invitation of user3 to ws1 has been revoked
    await f.create_workspace_invitation(
        email=user3.email,
        user=None,
        workspace=ws1,
        role=ws1_member_role,
        invited_by=user1,
        status=InvitationStatus.REVOKED,
    )

    # user1 invites user2 and user3 to a project in ws2
    pj1_ws2 = await f.create_project(
        template=project_template, name="pj1_ws2", workspace=ws2, created_by=user1
    )
    pj1_ws2_member_role = await pj1_ws2.roles.aget(slug="member")
    for user in (user2, user3):
        await f.create_project_invitation(
            email=user.email,
            user=user,
            project=pj1_ws2,
            role=pj1_ws2_member_role,
            invited_by=user1,
        )

    # user1 invites user2 and user3 to ws3 (mail only) and invite user2 to a project
    ws3_member_role = await ws3.roles.aget(slug="member")
    for user in (user2, user3):
        await f.create_workspace_invitation(
            email=user.email,
            user=None,
            workspace=ws3,
            role=ws3_member_role,
            invited_by=user1,
        )
    pj1_ws3 = await f.create_project(
        template=project_template, name="pj1_ws3", workspace=ws3, created_by=user1
    )
    pj1_ws3_member_role = await pj1_ws3.roles.aget(slug="member")
    await f.create_project_invitation(
        email=user2.email,
        user=None,
        project=pj1_ws3,
        role=pj1_ws3_member_role,
        invited_by=user1,
    )
    # add more projects
    pj2_ws3 = await f.create_project(
        template=project_template, name="pj2_ws3", workspace=ws3, created_by=user1
    )
    pj3_ws3 = await f.create_project(
        template=project_template, name="pj3_ws3", workspace=ws3, created_by=user1
    )

    # user1 invites user2 to ws4
    ws4_member_role = await ws4.roles.aget(slug="member")
    await f.create_workspace_invitation(
        email=user2.email,
        user=user2,
        workspace=ws4,
        role=ws4_member_role,
        invited_by=user1,
    )
    # invitation of user3 to ws4 has been denied
    await f.create_workspace_invitation(
        email=user3.email,
        user=user3,
        workspace=ws4,
        role=ws4_member_role,
        invited_by=user1,
        status=InvitationStatus.DENIED,
    )
    # add more projects
    pj1_ws4 = await f.create_project(
        template=project_template, name="pj1_ws4", workspace=ws4, created_by=user1
    )

    # ASSERTS
    # user1
    # owner of all workspaces and projects
    res = await repositories.list_user_workspaces_overview(user1)
    assert [ws.name for ws in res] == [ws5.name, ws4.name, ws3.name, ws2.name, ws1.name]
    assert not any(ws.is_invited for ws in res)
    assert [pj.name for pj in res[0].user_member_projects] == []  # ws5
    assert [pj.name for pj in res[1].user_member_projects] == [pj1_ws4.name]  # ws4
    assert [pj.name for pj in res[2].user_member_projects] == [
        pj3_ws3.name,
        pj2_ws3.name,
        pj1_ws3.name,
    ]  # ws3
    assert [pj.name for pj in res[3].user_member_projects] == [pj1_ws2.name]  # ws2
    assert [pj.name for pj in res[4].user_member_projects] == [
        pj3_ws1.name,
        pj2_ws1.name,
        pj1_ws1.name,
    ]  # ws1
    assert not any(ws.user_invited_projects for ws in res)
    # user2
    # member of ws: ws1; pj: pj1_ws1
    # invited to ws: ws3, ws4; pj: pj3_ws1, pj1_ws2, pj1_ws3
    res = await repositories.list_user_workspaces_overview(user2)
    assert [ws.name for ws in res] == [ws1.name, ws4.name, ws3.name, ws2.name]
    assert [ws.is_invited for ws in res] == [False, True, True, False]
    assert [pj.name for pj in res[0].user_member_projects] == [pj1_ws1.name]  # ws1
    assert not any(ws.user_member_projects for ws in res[1:])  # ws4, ws3, ws2

    assert [pj.name for pj in res[0].user_invited_projects] == [pj3_ws1.name]  # ws1
    assert [pj.name for pj in res[1].user_invited_projects] == []  # ws4
    assert [pj.name for pj in res[2].user_invited_projects] == [pj1_ws3.name]  # ws3
    assert [pj.name for pj in res[3].user_invited_projects] == [pj1_ws2.name]  # ws2
    # user3
    # member of none,
    # invited to ws: ws3; pj: pj2_ws1, pj1_ws2
    res = await repositories.list_user_workspaces_overview(user3)
    assert [ws.name for ws in res] == [ws3.name, ws2.name, ws1.name]
    assert [ws.is_invited for ws in res] == [True, False, False]
    assert not any(ws.user_member_projects for ws in res)

    assert [pj.name for pj in res[0].user_invited_projects] == []  # ws3
    assert [pj.name for pj in res[1].user_invited_projects] == [pj1_ws2.name]  # ws2
    assert [pj.name for pj in res[2].user_invited_projects] == [pj2_ws1.name]  # ws1


##########################################################
# get_workspace
##########################################################


async def test_get_workspace_return_workspace():
    workspace = await f.create_workspace(name="ws 1")
    assert await repositories.get_workspace(workspace_id=workspace.id) == workspace


async def test_get_workspace_return_none():
    non_existing_ws_id = uuid.uuid1()
    await f.create_workspace(name="ws 1")
    with pytest.raises(Workspace.DoesNotExist):
        await repositories.get_workspace(workspace_id=non_existing_ws_id)


##########################################################
# update workspace
##########################################################


async def test_update_workspace():
    workspace = await f.create_workspace()
    updated_workspace = await repositories.update_workspace(
        workspace=workspace,
        values={"name": "New name"},
    )
    assert updated_workspace.name == "New name"


##########################################################
# delete_workspace
##########################################################


async def test_delete_workspaces_without_ws_members():
    workspace = await f.create_workspace()

    num_deleted_wss = await repositories.delete_workspace(workspace_id=workspace.id)
    assert num_deleted_wss == 6  # 1 workspace, 1 ws_memberships, 4 ws_role


async def test_delete_workspaces_with_ws_members():
    workspace = await f.create_workspace()

    ws_member = await f.create_user()
    await f.create_workspace_membership(
        user=ws_member,
        workspace=workspace,
        role=await workspace.roles.filter(is_owner=False).afirst(),
    )

    num_deleted_wss = await repositories.delete_workspace(workspace_id=workspace.id)
    assert num_deleted_wss == 7  # 1 workspace, 2 ws_memberships, 4 ws_role
