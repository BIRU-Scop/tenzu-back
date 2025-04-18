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
from projects.projects.models import Project
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


async def test_list_workspace_projects_for_user(project_template):
    workspace = await f.create_workspace()
    project = await f.create_project(
        template=project_template, workspace=workspace, created_by=workspace.created_by
    )
    await f.create_project(
        template=project_template, workspace=workspace, created_by=workspace.created_by
    )
    await f.create_project(
        template=project_template, workspace=workspace, created_by=workspace.created_by
    )
    (
        member_projects,
        invited_projects,
    ) = await repositories.list_workspace_projects_for_user(
        workspace, workspace.created_by
    )
    # owner of project can see them all
    assert len(member_projects) == 3
    assert len(invited_projects) == 0

    user = await f.create_user()
    (
        member_projects,
        invited_projects,
    ) = await repositories.list_workspace_projects_for_user(workspace, user)
    # user has no projects
    assert len(member_projects) == 0
    assert len(invited_projects) == 0
    invitation = await f.create_project_invitation(user=user, project=project)
    (
        member_projects,
        invited_projects,
    ) = await repositories.list_workspace_projects_for_user(workspace, user)
    # user has been invited to one project
    assert len(member_projects) == 0
    assert len(invited_projects) == 1
    await f.create_project_membership(user=user, project=project)
    (
        member_projects,
        invited_projects,
    ) = await repositories.list_workspace_projects_for_user(workspace, user)
    # user has become member of one project and previous invitation still exists
    # (this should not happen but we still want project to appear in both list)
    assert len(member_projects) == 1
    assert len(invited_projects) == 1
    invitation.status = InvitationStatus.ACCEPTED
    await invitation.asave()
    (
        member_projects,
        invited_projects,
    ) = await repositories.list_workspace_projects_for_user(workspace, user)
    # user has become member of one project and previous invitation has been accepted
    assert len(member_projects) == 1
    assert len(invited_projects) == 0


##########################################################
# get_project
##########################################################


async def test_get_project_return_project(project_template):
    project = await f.create_project(template=project_template, name="Project 1")
    assert await repositories.get_project(project_id=project.id) == project


async def test_get_project_return_none():
    non_existent_id = uuid1()
    with pytest.raises(Project.DoesNotExist):
        await repositories.get_project(project_id=non_existent_id)


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
