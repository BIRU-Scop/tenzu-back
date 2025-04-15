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
from unittest import IsolatedAsyncioTestCase

import pytest

from projects.projects.models import ProjectTemplate
from tests.utils import factories as f
from workspaces.workspaces import repositories

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
# list_workspaces
##########################################################


async def test_list_workspaces_user_only_member_with_projects(project_template):
    user = await f.create_user()
    other_user = await f.create_user()
    # user only ws member with projects
    ws1 = await f.create_workspace(created_by=user)
    await f.create_project(template=project_template, created_by=user, workspace=ws1)
    await f.create_project(template=project_template, created_by=user, workspace=ws1)
    # user only ws member with projects
    ws2 = await f.create_workspace(created_by=user)
    await f.create_project(template=project_template, created_by=user, workspace=ws2)
    # user only ws member without projects
    await f.create_workspace(created_by=user)
    # user not only ws member with projects
    ws4 = await f.create_workspace(created_by=user)
    await f.create_workspace_membership(user=other_user, workspace=ws4)
    await f.create_project(template=project_template, created_by=user, workspace=ws4)
    # user not only ws member without projects
    ws5 = await f.create_workspace(created_by=user)
    await f.create_workspace_membership(user=other_user, workspace=ws5)

    ws_list = await repositories.list_workspaces(
        user=user, prefetch_related=["projects"], has_projects=True, is_only_user=True
    )

    assert len(ws_list) == 2
    assert ws_list[0].name == ws2.name
    assert ws_list[1].name == ws1.name


async def test_list_workspaces_user_only_member_without_projects(project_template):
    user = await f.create_user()
    other_user = await f.create_user()
    # user only ws member with projects
    ws1 = await f.create_workspace(created_by=user)
    await f.create_project(template=project_template, created_by=user, workspace=ws1)
    await f.create_project(template=project_template, created_by=user, workspace=ws1)
    # user only ws member with projects
    ws2 = await f.create_workspace(created_by=user)
    await f.create_project(template=project_template, created_by=user, workspace=ws2)
    # user only ws member without projects
    ws3 = await f.create_workspace(created_by=user)
    # user not only ws member with projects
    ws4 = await f.create_workspace(created_by=user)
    await f.create_workspace_membership(user=other_user, workspace=ws4)
    await f.create_project(template=project_template, created_by=user, workspace=ws4)
    # user not only ws member without projects
    ws5 = await f.create_workspace(created_by=user)
    await f.create_workspace_membership(user=other_user, workspace=ws5)

    ws_list = await repositories.list_workspaces(
        user=user, prefetch_related=["projects"], has_projects=False, is_only_user=True
    )

    assert len(ws_list) == 1
    assert ws_list[0].name == ws3.name


##########################################################
# get_workspace
##########################################################


async def test_get_workspace_return_workspace():
    workspace = await f.create_workspace(name="ws 1")
    assert await repositories.get_workspace(workspace_id=workspace.id) == workspace


async def test_get_workspace_return_none():
    non_existing_ws_id = uuid.uuid1()
    await f.create_workspace(name="ws 1")
    assert await repositories.get_workspace(workspace_id=non_existing_ws_id) is None


##########################################################
# get_workspace_detail
##########################################################


async def test_get_workspace_detail_no_projects():
    user12 = await f.create_user()

    # workspace, user12(ws-member), empty
    workspace4 = await f.create_workspace(name="workspace4", created_by=user12)
    res_ws = await repositories.get_workspace_detail(
        user_id=user12.id,
        workspace_id=workspace4.id,
    )
    assert res_ws == workspace4
    assert res_ws.has_projects is False


async def test_get_workspace_detail_projects(project_template):
    user13 = await f.create_user()
    user14 = await f.create_user()

    # workspace, user13(ws-member)
    workspace5 = await f.create_workspace(name="workspace5", created_by=user13)
    # user14 is a pj-admin
    await f.create_project(
        template=project_template, name="pj50", workspace=workspace5, created_by=user14
    )
    # user14 is pj-member
    pj51 = await f.create_project(
        template=project_template, name="pj51", workspace=workspace5, created_by=user13
    )
    pj_member_role = await pj51.roles.aget(slug="member")
    await f.create_project_membership(user=user14, project=pj51, role=pj_member_role)
    # user14 is pj-member, ws-members dont have permissions
    pj52 = await f.create_project(
        template=project_template, name="pj52", workspace=workspace5, created_by=user13
    )
    pj_member_role = await pj52.roles.aget(slug="member")
    await f.create_project_membership(user=user14, project=pj52, role=pj_member_role)
    pj_member_role.permissions = []
    await pj_member_role.asave()
    # user14 is not a pj-member
    await f.create_project(
        template=project_template, name="pj53", workspace=workspace5, created_by=user13
    )

    # assert workspace5 - user13
    res_ws = await repositories.get_workspace_detail(
        user_id=user13.id,
        workspace_id=workspace5.id,
    )
    assert res_ws == workspace5
    assert res_ws.has_projects is True
    # assert workspace5 - user14
    res_ws = await repositories.get_workspace_detail(
        user_id=user14.id,
        workspace_id=workspace5.id,
    )
    assert res_ws == workspace5
    assert res_ws.has_projects is True


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
# misc - get_user_workspaces_overview
##########################################################


async def test_get_user_workspaces_overview_latest_projects(project_template):
    user6 = await f.create_user()
    user7 = await f.create_user()

    # workspace, user6(ws-member) user7(not ws-member)
    workspace1 = await f.create_workspace(name="workspace1", created_by=user6)
    # user7 is a pj-admin
    await f.create_project(
        template=project_template, name="pj10", workspace=workspace1, created_by=user7
    )
    # user7 is pj-member
    pj11 = await f.create_project(
        template=project_template, name="pj11", workspace=workspace1, created_by=user6
    )
    pj_member_role = await pj11.roles.aget(slug="member")
    await f.create_project_membership(user=user7, project=pj11, role=pj_member_role)
    # user7 is pj-member without permissions to her pj-role
    pj12 = await f.create_project(
        template=project_template, name="pj12", workspace=workspace1, created_by=user6
    )
    pj_member_role = await pj12.roles.aget(slug="member")
    await f.create_project_membership(user=user7, project=pj12, role=pj_member_role)
    pj_member_role.permissions = []
    await pj_member_role.asave()
    await pj12.asave()
    # user7 is not a pj-member
    await f.create_project(
        template=project_template, name="pj15", workspace=workspace1, created_by=user6
    )

    # workspace, user6(ws-member), user7(not ws-member)
    workspace2 = await f.create_workspace(name="workspace2", created_by=user6)
    await f.create_project(
        template=project_template, workspace=workspace2, created_by=user6
    )

    # workspace, user6(ws-member), user7(ws-member, has_projects: false)
    workspace3 = await f.create_workspace(name="workspace3", created_by=user6)
    await f.create_workspace_membership(user=user7, workspace=workspace3)

    # workspace, user7(ws-member), empty
    workspace4 = await f.create_workspace(name="workspace4", created_by=user7)

    # workspace, user6(ws-member), user7(not ws-member)
    workspace5 = await f.create_workspace(name="workspace5", created_by=user6)
    # user7 is a pj-admin
    await f.create_project(
        template=project_template, name="pj50", workspace=workspace5, created_by=user7
    )
    # user7 is pj-member
    pj51 = await f.create_project(
        template=project_template, name="pj51", workspace=workspace5, created_by=user6
    )
    pj_member_role = await pj51.roles.aget(slug="member")
    await f.create_project_membership(user=user7, project=pj51, role=pj_member_role)
    # user7 is not a pj-member
    await f.create_project(
        template=project_template, name="pj53", workspace=workspace5, created_by=user6
    )

    # workspace, user6(ws-member), user7(not ws-member)
    workspace6 = await f.create_workspace(name="workspace6", created_by=user6)
    # user7 is NOT a pj-member
    await f.create_project(
        template=project_template, workspace=workspace6, created_by=user6
    )

    # workspace that shouldn't appear to anyone
    workspace7 = await f.create_workspace(name="workspace7")
    # user6 and user7 are not pj-member
    await f.create_project(template=project_template, workspace=workspace7)

    res = await repositories.list_user_workspaces_overview(user6)

    assert len(res) == 5  # workspaces

    names = [ws.name for ws in res]
    assert "workspace4" not in names
    assert "workspace7" not in names

    for ws in res:
        if ws.name == workspace1.name:
            assert ws.total_projects == 4
        elif ws.name == workspace2.name:
            assert ws.total_projects == 1
        elif ws.name == workspace3.name:
            assert ws.total_projects == 0
            assert ws.has_projects is False
        elif ws.name == workspace5.name:
            assert ws.total_projects == 3
        elif ws.name == workspace6.name:
            assert ws.total_projects == 1

    res = await repositories.list_user_workspaces_overview(user7)
    # A ws-member should see all her workspaces, and all the workspace's projects
    assert len(res) == 4  # workspaces

    names = [ws.name for ws in res]
    assert "workspace6" not in names
    assert "workspace7" not in names

    for ws in res:
        if ws.name == workspace1.name:
            assert ws.total_projects == 3
        elif ws.name == workspace3.name:
            assert ws.total_projects == 0
            assert ws.has_projects is False
        elif ws.name == workspace4.name:
            assert ws.total_projects == 0
        elif ws.name == workspace5.name:
            assert ws.total_projects == 2


async def test_get_user_workspaces_overview_invited_projects(project_template):
    user8 = await f.create_user()
    user9 = await f.create_user()
    user10 = await f.create_user()

    # user8 is member of several workspaces
    ws1 = await f.create_workspace(name="ws1 for member", created_by=user8)
    ws3 = await f.create_workspace(name="ws3 for guest", created_by=user8)
    ws4 = await f.create_workspace(name="ws4 for invited", created_by=user8)

    # user9 is member of ws1 as well
    await f.create_workspace_membership(user=user9, workspace=ws1)
    # user9 is guest of ws3
    pj = await f.create_project(
        template=project_template, name="pj1", workspace=ws3, created_by=user8
    )
    pj_member_role = await pj.roles.aget(slug="member")
    await f.create_project_membership(user=user9, project=pj, role=pj_member_role)

    # user8 invites user9 to a project in ws1
    pj = await f.create_project(
        template=project_template, name="pj2", workspace=ws1, created_by=user8
    )
    pj_member_role = await pj.roles.aget(slug="member")
    await f.create_project_invitation(
        email=user9.email,
        user=user9,
        project=pj,
        role=pj_member_role,
        invited_by=user8,
    )

    # user8 invites user10 to a project in ws1 (just email)
    pj = await f.create_project(
        template=project_template, name="pj3", workspace=ws1, created_by=user8
    )
    pj_member_role = await pj.roles.aget(slug="member")
    await f.create_project_invitation(
        email=user10.email,
        user=None,
        project=pj,
        role=pj_member_role,
        invited_by=user8,
    )

    # user8 invites user9 and user10 to a project in ws3
    pj = await f.create_project(
        template=project_template, name="pj4", workspace=ws3, created_by=user8
    )
    pj_member_role = await pj.roles.aget(slug="member")
    await f.create_project_invitation(
        email=user9.email,
        user=user9,
        project=pj,
        role=pj_member_role,
        invited_by=user8,
    )
    await f.create_project_invitation(
        email=user10.email,
        user=user10,
        project=pj,
        role=pj_member_role,
        invited_by=user8,
    )

    # user8 invites user9 and user10 to a project in ws4 (just email)
    pj = await f.create_project(
        template=project_template, name="pj5", workspace=ws4, created_by=user8
    )
    pj_member_role = await pj.roles.aget(slug="member")
    await f.create_project_invitation(
        email=user9.email, user=None, project=pj, role=pj_member_role, invited_by=user8
    )
    await f.create_project_invitation(
        email=user10.email,
        user=None,
        project=pj,
        role=pj_member_role,
        invited_by=user8,
    )

    # user 9
    res = await repositories.list_user_workspaces_overview(user9)

    assert len(res) == 3  # workspaces
    for ws in res:
        assert len(ws.invited_projects) == 1

    # user 10
    res = await repositories.list_user_workspaces_overview(user10)

    assert len(res) == 3  # workspaces
    for ws in res:
        assert len(ws.invited_projects) == 1


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


##########################################################
# misc - get_user_workspace_overview
##########################################################


class GetUserWorkspaceOverview(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.user1 = await f.create_user()
        self.user2 = await f.create_user()
        self.user3 = await f.create_user()
        self.project_template = await ProjectTemplate.objects.afirst()

    async def _asyncSetUp_workspace1(self):
        # workspace1: self.user1(ws-member), self.user2(not a ws-member)
        workspace1 = await f.create_workspace(name="workspace1", created_by=self.user1)
        # self.user2 is a pj-admin
        await f.create_project(
            template=self.project_template,
            name="pj10",
            workspace=workspace1,
            created_by=self.user2,
        )
        # self.user2 is pj-member
        pj11 = await f.create_project(
            template=self.project_template,
            name="pj11",
            workspace=workspace1,
            created_by=self.user1,
        )
        pj_member_role = await pj11.roles.aget(slug="member")
        await f.create_project_membership(
            user=self.user2, project=pj11, role=pj_member_role
        )
        # self.user3 is pj-invitee
        await f.create_project_invitation(
            email=self.user3.email,
            user=self.user3,
            project=pj11,
            role=pj_member_role,
            invited_by=self.user1,
        )

        # self.user2 is pj-member, ws-members have permissions
        pj12 = await f.create_project(
            template=self.project_template,
            name="pj12",
            workspace=workspace1,
            created_by=self.user1,
        )
        pj_member_role = await pj12.roles.aget(slug="member")
        await f.create_project_membership(
            user=self.user2, project=pj12, role=pj_member_role
        )
        pj_member_role.permissions = []
        await pj_member_role.asave()
        await pj12.asave()
        # self.user3 is pj-invitee
        await f.create_project_invitation(
            email=self.user3.email,
            user=self.user3,
            project=pj12,
            role=pj_member_role,
            invited_by=self.user2,
        )
        # self.user2 is pj-member, ws-members dont have permissions
        pj13 = await f.create_project(
            template=self.project_template,
            name="pj13",
            workspace=workspace1,
            created_by=self.user1,
        )
        pj_member_role = await pj13.roles.aget(slug="member")
        await f.create_project_membership(
            user=self.user2, project=pj13, role=pj_member_role
        )
        pj_member_role.permissions = []
        await pj_member_role.asave()
        # self.user2 is not a pj-member but the project allows 'view_story' to ws-members
        pj14 = await f.create_project(
            template=self.project_template,
            name="pj14",
            workspace=workspace1,
            created_by=self.user1,
        )
        await pj14.asave()
        # self.user2 is not a pj-member and ws-members are not allowed
        await f.create_project(
            template=self.project_template,
            name="pj15",
            workspace=workspace1,
            created_by=self.user1,
        )
        # self.user2 is a pj-admin
        pj16 = await f.create_project(
            template=self.project_template,
            name="pj16",
            workspace=workspace1,
            created_by=self.user2,
        )
        pj_member_role = await pj16.roles.aget(slug="member")
        # self.user1 is pj-invitee
        await f.create_project_invitation(
            email=self.user1.email,
            user=self.user1,
            project=pj16,
            role=pj_member_role,
            invited_by=self.user2,
        )
        # self.user3 is pj-invitee
        await f.create_project_invitation(
            email=self.user3.email,
            user=self.user3,
            project=pj16,
            role=pj_member_role,
            invited_by=self.user2,
        )
        await f.create_project(
            template=self.project_template,
            name="pj17",
            workspace=workspace1,
            created_by=self.user1,
        )
        await f.create_project(
            template=self.project_template,
            name="pj18",
            workspace=workspace1,
            created_by=self.user1,
        )
        await f.create_project(
            template=self.project_template,
            name="pj19",
            workspace=workspace1,
            created_by=self.user1,
        )
        await f.create_project(
            template=self.project_template,
            name="pj20",
            workspace=workspace1,
            created_by=self.user1,
        )
        await f.create_project(
            template=self.project_template,
            name="pj21",
            workspace=workspace1,
            created_by=self.user1,
        )
        await f.create_project(
            template=self.project_template,
            name="pj22",
            workspace=workspace1,
            created_by=self.user1,
        )
        await f.create_project(
            template=self.project_template,
            name="pj23",
            workspace=workspace1,
            created_by=self.user1,
        )
        self.workspace1 = workspace1

    async def _asyncSetUp_workspace2(self):
        # workspace2, self.user1(ws-member), self.user2(not a ws-member, has_projects: true)
        workspace2 = await f.create_workspace(name="workspace2", created_by=self.user1)
        # self.user2 is not a pj-member and ws-members are not allowed
        await f.create_project(
            template=self.project_template, workspace=workspace2, created_by=self.user1
        )
        self.workspace2 = workspace2

    async def _asyncSetUp_workspace3(self):
        # workspace3, self.user1(ws-member), self.user2(not a ws-member, has_projects: false)
        workspace3 = await f.create_workspace(name="workspace3", created_by=self.user1)
        self.workspace3 = workspace3

    async def _asyncSetUp_workspace4(self):
        # workspace4, self.user2(ws-member), empty
        workspace4 = await f.create_workspace(name="workspace4", created_by=self.user2)
        self.workspace4 = workspace4

    async def _asyncSetUp_workspace5(self):
        # workspace5, self.user1(ws-member), self.user2(NOT ws-member)
        workspace5 = await f.create_workspace(name="workspace5", created_by=self.user1)
        # self.user2 is a pj-admin
        await f.create_project(
            template=self.project_template,
            name="pj50",
            workspace=workspace5,
            created_by=self.user2,
        )
        # self.user2 is pj-member
        pj51 = await f.create_project(
            template=self.project_template,
            name="pj51",
            workspace=workspace5,
            created_by=self.user1,
        )
        pj_member_role = await pj51.roles.aget(slug="member")
        await f.create_project_membership(
            user=self.user2, project=pj51, role=pj_member_role
        )
        # self.user2 is pj-member, ws-members dont have permissions
        pj52 = await f.create_project(
            template=self.project_template,
            name="pj52",
            workspace=workspace5,
            created_by=self.user1,
        )
        pj_member_role = await pj52.roles.aget(slug="member")
        await f.create_project_membership(
            user=self.user2, project=pj52, role=pj_member_role
        )
        pj_member_role.permissions = []
        await pj_member_role.asave()
        # self.user2 is not a pj-member
        await f.create_project(
            template=self.project_template,
            name="pj53",
            workspace=workspace5,
            created_by=self.user1,
        )
        self.workspace5 = workspace5

    async def _asyncSetUp_workspace6(self):
        # workspace6, self.user1(ws-member), self.user2(NOT ws-member)
        workspace6 = await f.create_workspace(name="workspace6", created_by=self.user1)
        # self.user2 is NOT a pj-member
        await f.create_project(
            template=self.project_template, workspace=workspace6, created_by=self.user1
        )
        self.workspace6 = workspace6

    async def _asyncSetUp_workspace7(self):
        # workspace7 that shouldnt appear to anyone
        workspace7 = await f.create_workspace(name="workspace7")
        # self.user1 and self.user2 are NOT pj-member
        await f.create_project(template=self.project_template, workspace=workspace7)
        self.workspace7 = workspace7

    async def test_get_workspace1(self):
        await self._asyncSetUp_workspace1()

        ws = await repositories.get_user_workspace_overview(
            user=self.user1, id=self.workspace1.id
        )
        self.assertEqual(ws.name, self.workspace1.name)
        self.assertEqual(len(ws.latest_projects), 12)
        self.assertEqual(len(ws.invited_projects), 1)
        self.assertEqual(ws.total_projects, 14)
        self.assertTrue(ws.has_projects)
        self.assertEqual(ws.user_role, "member")

        ws = await repositories.get_user_workspace_overview(
            user=self.user2, id=self.workspace1.id
        )
        self.assertEqual(ws.name, self.workspace1.name)
        self.assertEqual(len(ws.latest_projects), 5)
        self.assertEqual(len(ws.invited_projects), 0)
        self.assertEqual(ws.total_projects, 5)
        self.assertTrue(ws.has_projects)
        self.assertEqual(ws.user_role, "guest")

        ws = await repositories.get_user_workspace_overview(
            user=self.user3, id=self.workspace1.id
        )
        self.assertEqual(ws.name, self.workspace1.name)
        self.assertEqual(len(ws.latest_projects), 0)
        self.assertEqual(len(ws.invited_projects), 3)
        self.assertEqual(ws.total_projects, 0)
        self.assertTrue(ws.has_projects)
        self.assertEqual(ws.user_role, "guest")

    async def test_get_workspace2(self):
        await self._asyncSetUp_workspace2()

        ws = await repositories.get_user_workspace_overview(
            user=self.user1, id=self.workspace2.id
        )
        self.assertEqual(ws.name, self.workspace2.name)
        self.assertEqual(len(ws.latest_projects), 1)
        self.assertEqual(len(ws.invited_projects), 0)
        self.assertEqual(ws.total_projects, 1)
        self.assertTrue(ws.has_projects)
        self.assertEqual(ws.user_role, "member")

        ws = await repositories.get_user_workspace_overview(
            user=self.user2, id=self.workspace2.id
        )
        self.assertIsNone(ws)

        ws = await repositories.get_user_workspace_overview(
            user=self.user3, id=self.workspace2.id
        )
        self.assertIsNone(ws)

    async def test_get_workspace3(self):
        await self._asyncSetUp_workspace3()

        ws = await repositories.get_user_workspace_overview(
            user=self.user1, id=self.workspace3.id
        )
        self.assertEqual(ws.name, self.workspace3.name)
        self.assertEqual(len(ws.latest_projects), 0)
        self.assertEqual(len(ws.invited_projects), 0)
        self.assertEqual(ws.total_projects, 0)
        self.assertFalse(ws.has_projects)
        self.assertEqual(ws.user_role, "member")

        ws = await repositories.get_user_workspace_overview(
            user=self.user2, id=self.workspace3.id
        )
        self.assertIsNone(ws)

        ws = await repositories.get_user_workspace_overview(
            user=self.user3, id=self.workspace3.id
        )
        self.assertIsNone(ws)

    async def test_get_workspace4(self):
        await self._asyncSetUp_workspace4()

        ws = await repositories.get_user_workspace_overview(
            user=self.user1, id=self.workspace4.id
        )
        self.assertIsNone(ws)

        ws = await repositories.get_user_workspace_overview(
            user=self.user2, id=self.workspace4.id
        )
        self.assertEqual(ws.name, self.workspace4.name)
        self.assertEqual(len(ws.latest_projects), 0)
        self.assertEqual(len(ws.invited_projects), 0)
        self.assertEqual(ws.total_projects, 0)
        self.assertFalse(ws.has_projects)
        self.assertEqual(ws.user_role, "member")

        ws = await repositories.get_user_workspace_overview(
            user=self.user3, id=self.workspace4.id
        )
        self.assertIsNone(ws)

    async def test_get_workspace5(self):
        await self._asyncSetUp_workspace5()

        ws = await repositories.get_user_workspace_overview(
            user=self.user1, id=self.workspace5.id
        )
        self.assertEqual(ws.name, self.workspace5.name)
        self.assertEqual(len(ws.latest_projects), 4)
        self.assertEqual(len(ws.invited_projects), 0)
        self.assertEqual(ws.total_projects, 4)
        self.assertTrue(ws.has_projects)
        self.assertEqual(ws.user_role, "member")

        ws = await repositories.get_user_workspace_overview(
            user=self.user2, id=self.workspace5.id
        )
        self.assertEqual(ws.name, self.workspace5.name)
        self.assertEqual(len(ws.latest_projects), 3)
        self.assertEqual(len(ws.invited_projects), 0)
        self.assertEqual(ws.total_projects, 3)
        self.assertTrue(ws.has_projects)
        self.assertEqual(ws.user_role, "guest")

        ws = await repositories.get_user_workspace_overview(
            user=self.user3, id=self.workspace5.id
        )
        self.assertIsNone(ws)

    async def test_get_workspace6(self):
        await self._asyncSetUp_workspace6()

        ws = await repositories.get_user_workspace_overview(
            user=self.user1, id=self.workspace6.id
        )
        self.assertEqual(ws.name, self.workspace6.name)
        self.assertEqual(len(ws.latest_projects), 1)
        self.assertEqual(len(ws.invited_projects), 0)
        self.assertEqual(ws.total_projects, 1)
        self.assertTrue(ws.has_projects)
        self.assertEqual(ws.user_role, "member")

        ws = await repositories.get_user_workspace_overview(
            user=self.user2, id=self.workspace6.id
        )
        self.assertIsNone(ws)

        ws = await repositories.get_user_workspace_overview(
            user=self.user3, id=self.workspace6.id
        )
        self.assertIsNone(ws)

    async def test_get_workspace7(self):
        await self._asyncSetUp_workspace7()

        ws = await repositories.get_user_workspace_overview(
            user=self.user1, id=self.workspace7.id
        )
        self.assertIsNone(ws)

        ws = await repositories.get_user_workspace_overview(
            user=self.user2, id=self.workspace7.id
        )
        self.assertIsNone(ws)

        ws = await repositories.get_user_workspace_overview(
            user=self.user3, id=self.workspace7.id
        )
        self.assertIsNone(ws)


##########################################################
# list_workspace_projects
##########################################################


async def test_list_workspace_projects(project_template):
    workspace = await f.create_workspace()
    await f.create_project(template=project_template, workspace=workspace)
    await f.create_project(template=project_template, workspace=workspace)

    projects = await repositories.list_workspace_projects(workspace=workspace)

    assert len(projects) == 2
