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
from uuid import uuid1

import pytest
from asgiref.sync import sync_to_async
from django.core.files import File
from django.db import models

from base.db import sequences as seq
from memberships.choices import InvitationStatus
from projects import references
from projects.projects import repositories
from tests.utils import factories as f

pytestmark = pytest.mark.django_db


##########################################################
# create_project
##########################################################


async def test_create_project():
    workspace = await f.create_workspace()
    project = await repositories.create_project(
        name="My test project",
        description="",
        color=3,
        created_by=workspace.created_by,
        workspace=workspace,
        landing_page="",
    )
    assert project.slug == "my-test-project"
    assert await _seq_exists(references.get_project_references_seqname(project.id))


async def test_create_project_with_non_ASCI_chars():
    workspace = await f.create_workspace()
    project = await repositories.create_project(
        name="My proj#%&乕شect",
        description="",
        color=3,
        created_by=workspace.created_by,
        workspace=workspace,
        landing_page="",
    )
    assert project.slug == "my-proj-hu-shect"
    assert await _seq_exists(references.get_project_references_seqname(project.id))


async def test_create_project_with_logo():
    image_file = f.build_image_file()
    workspace = await f.create_workspace()
    project = await repositories.create_project(
        name="My test project",
        description="",
        color=3,
        created_by=workspace.created_by,
        workspace=workspace,
        logo=image_file,
        landing_page="",
    )
    assert project.logo.name.endswith(image_file.name)
    assert await _seq_exists(references.get_project_references_seqname(project.id))


async def test_create_project_with_no_logo():
    workspace = await f.create_workspace()
    project = await repositories.create_project(
        name="My test project",
        description="",
        color=3,
        created_by=workspace.created_by,
        workspace=workspace,
        logo=None,
        landing_page="",
    )
    assert project.logo == File(None)
    assert await _seq_exists(references.get_project_references_seqname(project.id))


##########################################################
# list projects
##########################################################


async def test_list_workspace_invited_projects_for_user(project_template):
    user8 = await f.create_user()
    user9 = await f.create_user()

    # workspace, user8(ws-member), user9(ws-member)
    workspace = await f.create_workspace(created_by=user8)
    await f.create_workspace_membership(user=user9, workspace=workspace)
    # user8 is a pj-admin of several projects
    pj1 = await f.create_project(
        template=project_template, workspace=workspace, created_by=user8
    )
    await f.create_project(
        template=project_template, workspace=workspace, created_by=user8
    )
    pj3 = await f.create_project(
        template=project_template, workspace=workspace, created_by=user8
    )
    # user8 invites user9 to several projects
    await f.create_project_invitation(
        email=user9.email, user=user9, project=pj1, invited_by=user8
    )
    await f.create_project_invitation(
        email=user9.email, user=user9, project=pj3, invited_by=user8
    )

    res = await repositories.list_projects(
        filters={
            "workspace_id": workspace.id,
            "invitations__user_id": user9.id,
            "invitations__status": InvitationStatus.PENDING,
        },
    )
    assert len(res) == 2
    assert res[0].name == pj3.name
    assert res[1].name == pj1.name


async def test_list_projects(project_template):
    workspace = await f.create_workspace()
    await f.create_project(
        template=project_template, workspace=workspace, created_by=workspace.created_by
    )
    await f.create_project(
        template=project_template, workspace=workspace, created_by=workspace.created_by
    )
    await f.create_project(
        template=project_template, workspace=workspace, created_by=workspace.created_by
    )
    res = await repositories.list_projects(filters={"workspace_id": workspace.id})
    assert len(res) == 3


async def test_list_workspace_projects_for_user_1(project_template):
    user6 = await f.create_user()
    user7 = await f.create_user()

    # workspace, user6(ws-member)
    workspace = await f.create_workspace(created_by=user6)
    # user7 is a pj-admin
    await f.create_project(
        template=project_template, workspace=workspace, created_by=user7
    )
    # user7 is pj-member
    pj11 = await f.create_project(
        template=project_template, workspace=workspace, created_by=user6
    )
    pj_member_role = await pj11.roles.aget(slug="member")
    await f.create_project_membership(user=user7, project=pj11, role=pj_member_role)
    # user7 is not a pj-member
    pj14 = await f.create_project(
        template=project_template, workspace=workspace, created_by=user6
    )
    await pj14.asave()

    # A ws-member should see every project in her workspaces
    res = await repositories.list_projects(filters={"workspace_id": workspace.id})
    assert len(res) == 3
    # Not ws-member users should see just the projects in which she's a pj-member
    res = await repositories.list_projects(
        filters={"workspace_id": workspace.id, "memberships__user_id": user7.id}
    )
    assert len(res) == 2


async def test_list_projects_2(project_template):
    user6 = await f.create_user()
    user7 = await f.create_user()

    # workspace, user6(ws-member), user7(ws-member, has_projects: true)
    workspace = await f.create_workspace(created_by=user6)
    await f.create_workspace_membership(user=user7, workspace=workspace)
    # user7 is not a pj-member and ws-members are not allowed
    await f.create_project(
        template=project_template, workspace=workspace, created_by=user6
    )

    res = await repositories.list_projects(
        filters={"workspace_id": workspace.id, "memberships__user_id": user6.id}
    )
    assert len(res) == 1
    res = await repositories.list_projects(
        filters={"workspace_id": workspace.id, "memberships__user_id": user7.id}
    )
    assert len(res) == 0


async def test_list_workspace_projects_for_user_3():
    user6 = await f.create_user()
    user7 = await f.create_user()

    # workspace, user6(ws-member), user7(ws-member, has_projects: false)
    workspace = await f.create_workspace(created_by=user6)
    await f.create_workspace_membership(user=user7, workspace=workspace)

    res = await repositories.list_projects(
        filters={"workspace_id": workspace.id, "memberships__user_id": user6.id}
    )
    assert len(res) == 0
    res = await repositories.list_projects(
        filters={"workspace_id": workspace.id, "memberships__user_id": user7.id}
    )
    assert len(res) == 0


async def test_list_workspace_projects_for_user_4(project_template):
    user6 = await f.create_user()
    user7 = await f.create_user()

    # workspace, user6(ws-member), user7(no ws-member, ws-members have permissions)
    workspace = await f.create_workspace(created_by=user6)
    # user7 is not a pj-member or ws-member but ws-members are allowed
    await f.create_project(
        template=project_template, workspace=workspace, created_by=user6
    )

    res = await repositories.list_projects(
        filters={"workspace_id": workspace.id, "memberships__user_id": user6.id}
    )
    assert len(res) == 1
    res = await repositories.list_projects(
        filters={"workspace_id": workspace.id, "memberships__user_id": user7.id}
    )
    assert len(res) == 0


##########################################################
# get_project
##########################################################


async def test_get_project_return_project(project_template):
    project = await f.create_project(template=project_template, name="Project 1")
    assert await repositories.get_project(project_id=project.id) == project


async def test_get_project_return_none():
    non_existent_id = uuid1()
    assert await repositories.get_project(project_id=non_existent_id) is None


##########################################################
# update project
##########################################################


async def test_update_project(project_template):
    project = await f.create_project(template=project_template, name="Project 1")
    assert project.name == "Project 1"
    updated_project = await repositories.update_project(
        project=project,
        values={"name": "New name", "description": "New description"},
    )
    assert updated_project.name == "New name"
    assert updated_project.description == "New description"


async def test_update_project_delete_description(project_template):
    project = await f.create_project(template=project_template, name="Project 1")
    assert project.name == "Project 1"
    updated_project = await repositories.update_project(
        project,
        values={"description": ""},
    )
    assert updated_project.description == ""


async def test_update_project_delete_logo(project_template):
    project = await f.create_project(template=project_template, name="Project 1")
    assert project.logo is not None
    updated_project = await repositories.update_project(
        project,
        values={"logo": None},
    )
    assert updated_project.logo == models.FileField(None)


##########################################################
# delete_projects
##########################################################


async def test_delete_projects(project_template):
    project = await f.create_project(
        template=project_template,
    )
    await f.create_project_invitation(
        project=project, role=await project.roles.filter(is_owner=False).afirst()
    )
    seqname = references.get_project_references_seqname(project.id)

    assert await _seq_exists(seqname)
    deleted = await repositories.delete_projects(project_id=project.id)
    assert (
        deleted == 12
    )  # 1 project, 1 workflow, 4 statuses, 1 invitation, 1 membership, 4 roles
    assert not await _seq_exists(seqname)


##########################################################
# misc - get_total_projects
##########################################################


async def test_get_total_projects_in_ws(project_template) -> None:
    user1 = await f.create_user()
    other_user = await f.create_user()
    ws = await f.create_workspace(created_by=user1)
    await f.create_project(
        template=project_template, workspace=ws, created_by=other_user
    )
    await f.create_project(template=project_template, workspace=ws, created_by=user1)

    res = await repositories.get_total_projects(
        filters={"memberships__user_id": user1.id}, workspace_id=ws.id
    )
    assert res == 1


##########################################################
# get_first_workflow_slug
##########################################################


async def test_get_first_workflow_slug():
    project = await f.create_simple_project()
    assert await repositories.get_first_workflow_slug(project) is None
    workflow1 = await f.create_workflow(project=project, order=3)
    assert await repositories.get_first_workflow_slug(project) == workflow1.slug
    _ = await f.create_workflow(project=project, order=5)
    assert await repositories.get_first_workflow_slug(project) == workflow1.slug
    workflow3 = await f.create_workflow(project=project, order=2)
    assert await repositories.get_first_workflow_slug(project) == workflow3.slug


##########################################################
# Template: get_template
##########################################################


async def test_get_template_return_template():
    assert (
        await repositories.get_project_template(filters={"slug": "kanban"}) is not None
    )


##########################################################
# utils
##########################################################


_seq_exists = sync_to_async(seq.exists)
