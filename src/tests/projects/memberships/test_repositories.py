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

from memberships.services import exceptions as ex
from permissions import choices
from permissions.choices import ProjectPermissions
from projects.memberships import repositories
from projects.memberships.models import ProjectMembership, ProjectRole
from projects.projects.models import Project
from tests.utils import factories as f

pytestmark = pytest.mark.django_db


##########################################################
# create_project_membership
##########################################################


async def test_create_project_membership(project_template):
    user = await f.create_user()
    project = await f.create_project(project_template)
    await f.create_workspace_membership(user=user, workspace=project.workspace)
    role = await f.create_project_role(project=project)
    membership = await repositories.create_project_membership(
        user=user, project=project, role=role
    )
    memberships = [m async for m in project.memberships.all()]
    assert membership in memberships


async def test_create_project_membership_error_not_workspace_member(project_template):
    user = await f.create_user()
    project = await f.create_project(project_template)
    role = await f.create_project_role(project=project)
    with pytest.raises(ex.NoRelatedWorkspaceMembershipsError):
        await repositories.create_project_membership(
            user=user, project=project, role=role
        )


async def test_create_project_membership_error_not_belong(project_template):
    user = await f.create_user()
    project = await f.create_project(project_template)
    other_project = await f.create_project(project_template)
    role = await f.create_project_role(project=project)
    with pytest.raises(ex.MembershipWithRoleThatDoNotBelong):
        await repositories.create_project_membership(
            user=user, project=other_project, role=role
        )


##########################################################
# list_project_memberships
##########################################################


async def test_list_project_memberships(project_template):
    owner = await f.create_user()
    user1 = await f.create_user()
    user2 = await f.create_user()
    project = await f.create_project(project_template, created_by=owner)
    role = await f.create_project_role(project=project)
    await f.create_project_membership(user=user1, project=project, role=role)
    await f.create_project_membership(user=user2, project=project, role=role)

    memberships = await repositories.list_memberships(
        ProjectMembership, filters={"project_id": project.id}
    )
    assert len(memberships) == 3  # 2 explicitly created + owner membership


##########################################################
# get_project_membership
##########################################################


async def test_get_project_membership(project_template):
    user = await f.create_user()
    project = await f.create_project(project_template)
    role = await f.create_project_role(project=project)
    membership = await f.create_project_membership(
        user=user, project=project, role=role
    )

    ret_membership = repositories.get_membership(
        ProjectMembership,
        filters={"project_id": project.id, "user__username": user.username},
    )
    assert await ret_membership == membership

    membership = await repositories.get_membership(
        ProjectMembership,
        filters={
            "id": membership.id,
            "role__permissions__contains": [ProjectPermissions.VIEW_STORY.value],
        },
        select_related=["project", "user"],
    )
    assert membership.project == project
    assert membership.user == user


async def test_get_project_membership_doesnotexist():
    with pytest.raises(ProjectMembership.DoesNotExist):
        await repositories.get_membership(
            ProjectMembership,
            filters={"user_id": uuid.uuid1(), "project_id": uuid.uuid1()},
        )


##########################################################
# update_project_membership
##########################################################


async def test_update_project_membership(project_template):
    user = await f.create_user()
    project = await f.create_project(project_template)
    role = await f.create_project_role(project=project)
    membership = await f.create_project_membership(
        user=user, project=project, role=role
    )

    new_role = await f.create_project_role(project=project)
    updated_membership = await repositories.update_membership(
        membership=membership, values={"role": new_role}
    )
    assert updated_membership.role == new_role


##########################################################
# delete_project_membership
##########################################################


async def test_delete_project_membership(project_template) -> None:
    user = await f.create_user()
    project = await f.create_project(project_template)
    role = await f.create_project_role(project=project)
    membership = await f.create_project_membership(
        user=user, project=project, role=role
    )
    deleted = await repositories.delete_membership(membership)
    assert deleted == 1
    memberships = [m async for m in project.memberships.all()]
    assert len(memberships) == 1


##########################################################
# misc - has_other_owner_project_memberships
##########################################################


async def test_has_other_owner_project_memberships(project_template):
    user = await f.create_user()
    user2 = await f.create_user()
    project = await f.create_project(project_template)
    await f.create_project(project_template)
    owner_membership = await project.memberships.select_related("role").aget()
    role = await f.create_project_role(project=project)

    assert not await repositories.has_other_owner_memberships(owner_membership)

    await f.create_project_membership(user=user, project=project, role=role)
    assert not await repositories.has_other_owner_memberships(owner_membership)

    await f.create_project_membership(
        user=user2, project=project, role=owner_membership.role
    )
    assert await repositories.has_other_owner_memberships(owner_membership)


##########################################################
# misc - list_project_members
##########################################################


async def test_list_project_members(project_template):
    user = await f.create_user()
    project = await f.create_project(project_template)
    role = await f.create_project_role(project=project)

    project_member = await repositories.list_members(reference_object=project)
    assert len(project_member) == 1

    await f.create_project_membership(user=user, project=project, role=role)

    project_member = await repositories.list_members(reference_object=project)
    assert len(project_member) == 2


##########################################################
# misc - only_project_member_queryset
##########################################################


async def test_list_projects_user_only_member(project_template):
    user = await f.create_user()
    other_user = await f.create_user()
    ws1 = await f.create_workspace(created_by=user)
    # user only pj member
    pj1_ws1 = await f.create_project(
        template=project_template, created_by=user, workspace=ws1
    )
    # user only pj member
    pj2_ws1 = await f.create_project(
        template=project_template, created_by=user, workspace=ws1
    )
    ws2 = await f.create_workspace(created_by=user)
    # user only pj member
    pj1_ws2 = await f.create_project(
        template=project_template, created_by=user, workspace=ws2
    )
    ws3 = await f.create_workspace(created_by=user)
    # user owner not only pj member
    pj1_ws3 = await f.create_project(
        template=project_template, created_by=user, workspace=ws3
    )
    await f.create_project_membership(
        user=other_user,
        project=pj1_ws3,
    )
    # user not owner not only pj member
    pj2_ws3 = await f.create_project(
        template=project_template, created_by=other_user, workspace=ws3
    )
    await f.create_project_membership(
        user=user,
        project=pj2_ws3,
    )
    # user not member
    pj3_ws3 = await f.create_project(
        template=project_template, created_by=other_user, workspace=ws3
    )
    ws4 = await f.create_workspace(created_by=other_user)
    pj1_ws6 = await f.create_project(
        template=project_template, created_by=other_user, workspace=ws4
    )

    pj_list = [pj async for pj in repositories.only_project_member_queryset(user)]

    assert len(pj_list) == 3
    assert pj_list[0].name == pj1_ws1.name
    assert pj_list[1].name == pj2_ws1.name
    assert pj_list[2].name == pj1_ws2.name

    pj_list = [
        pj
        async for pj in repositories.only_project_member_queryset(
            user, excludes={"workspace__in": [ws1]}
        )
    ]

    assert len(pj_list) == 1
    assert pj_list[0].name == pj1_ws2.name


##########################################################
# misc - only_owner_collective_queryset
##########################################################


async def test_list_projects_user_only_owner_but_not_only_member(project_template):
    user = await f.create_user()
    other_user = await f.create_user()
    ws1 = await f.create_workspace(created_by=user)
    # user only pj member
    await f.create_project(template=project_template, created_by=user, workspace=ws1)
    # user only pj member
    await f.create_project(template=project_template, created_by=user, workspace=ws1)

    ws2 = await f.create_workspace(created_by=user)
    # user only pj member
    await f.create_project(template=project_template, created_by=user, workspace=ws2)

    ws3 = await f.create_workspace(created_by=user)
    await f.create_workspace_membership(user=other_user, workspace=ws3)
    # user only pj owner but not only member
    pj1_ws3 = await f.create_project(
        template=project_template, created_by=user, workspace=ws3
    )
    await f.create_project_membership(user=other_user, project=pj1_ws3)
    # user not only pj owner
    pj2_ws3 = await f.create_project(
        template=project_template, created_by=user, workspace=ws3
    )
    owner_role = await pj1_ws3.roles.aget(is_owner=True)
    await f.create_project_membership(user=other_user, project=pj2_ws3, role=owner_role)

    # user not member
    ws4 = await f.create_workspace(created_by=other_user)
    await f.create_project(
        template=project_template, created_by=other_user, workspace=ws4
    )
    # user not owner
    ws5 = await f.create_workspace(created_by=other_user)
    await f.create_workspace_membership(user=user, workspace=ws5)
    pj1_ws5 = await f.create_project(
        template=project_template, created_by=other_user, workspace=ws5
    )
    await f.create_project_membership(user=user, project=pj1_ws5)

    pj_list = [
        pj async for pj in repositories.only_owner_collective_queryset(Project, user)
    ]

    assert len(pj_list) == 1
    assert pj_list[0].name == pj1_ws3.name


##########################################################
# create_project_roles
##########################################################


async def test_create_project_roles(project_template):
    project = await f.create_project(project_template)
    project_role_res = await repositories.create_project_role(
        name="project-role",
        project_id=project.id,
        permissions=[],
    )
    assert project_role_res.name == "project-role"
    assert project_role_res.slug == "project-role"
    assert project_role_res.project == project
    assert not project_role_res.is_owner
    assert project_role_res.editable


async def test_bulk_create_project_roles(project_template):
    project = await f.create_project(project_template)
    project_roles_res = await repositories.bulk_create_project_roles(
        [
            ProjectRole(
                name="project-role",
                slug="project-role",
                order=1,
                project=project,
                permissions=[],
            )
        ]
    )
    assert len(project_roles_res) == 1
    assert project_roles_res[0].name == "project-role"
    assert project_roles_res[0].project == project
    assert not project_roles_res[0].is_owner
    assert project_roles_res[0].editable


##########################################################
# list_project_roles
##########################################################


async def test_list_project_roles(project_template):
    project = await f.create_project(project_template)
    res = await repositories.list_roles(ProjectRole, filters={"project_id": project.id})
    assert len(res) == 4
    assert sum(1 for role in res if role.is_owner) == 1
    assert all(not hasattr(role, "total_members") for role in res)
    res = await repositories.list_roles(
        ProjectRole, filters={"project_id": project.id}, get_total_members=True
    )
    assert len(res) == 4
    assert res[0].total_members == 1
    assert all(role.total_members == 0 for role in res[1:])


##########################################################
# get_project_role
##########################################################


async def test_get_project_role_return_role(project_template):
    project = await f.create_project(project_template)
    role = await f.create_project_role(
        name="Role test",
        slug="role-test",
        permissions=choices.ProjectPermissions.choices,
        is_owner=True,
        project=project,
    )
    assert (
        await repositories.get_role(
            ProjectRole, filters={"project_id": project.id, "slug": "role-test"}
        )
        == role
    )


async def test_get_project_role_return_doesnotexist(project_template):
    project = await f.create_project(project_template)
    with pytest.raises(ProjectRole.DoesNotExist):
        await repositories.get_role(
            ProjectRole, filters={"project_id": project.id, "slug": "role-not-exist"}
        )


async def test_get_project_role_for_user_owner(project_template):
    user = await f.create_user()
    project = await f.create_project(project_template, created_by=user)
    role = await project.roles.aget(slug="owner")

    assert (
        await repositories.get_role(
            ProjectRole,
            filters={"memberships__user_id": user.id, "project_id": project.id},
        )
        == role
    )


async def test_get_project_role_for_user_member(project_template):
    user = await f.create_user()
    project = await f.create_project(project_template)
    role = await project.roles.aget(slug="member")
    await f.create_project_membership(user=user, project=project, role=role)

    assert (
        await repositories.get_role(
            ProjectRole,
            filters={"memberships__user_id": user.id, "project_id": project.id},
        )
        == role
    )


async def test_get_project_role_for_user_doesnotexist(project_template):
    user = await f.create_user()
    project = await f.create_project(project_template)

    with pytest.raises(ProjectRole.DoesNotExist):
        await repositories.get_role(
            ProjectRole,
            filters={"memberships__user_id": user.id, "project_id": project.id},
        )


##########################################################
# update project role
##########################################################


async def test_update_project_role():
    role = await f.create_project_role()
    updated_role = await repositories.update_role(
        role=role,
        values={"permissions": [ProjectPermissions.VIEW_STORY.value]},
    )
    assert ProjectPermissions.VIEW_STORY.value in updated_role.permissions


##########################################################
# delete project role
##########################################################


async def test_delete_project_role():
    role = await f.create_project_role()
    deleted = await repositories.delete_project_role(
        role=role,
    )
    assert deleted == 1
    with pytest.raises(ProjectRole.DoesNotExist):
        await role.arefresh_from_db()


##########################################################
# misc project role
##########################################################


async def test_move_project_role_of_related():
    role = await f.create_project_role()
    target_role = await f.create_project_role(project=role.project)
    invitation = await f.create_project_invitation(role=role, project=role.project)
    membership = await f.create_project_membership(role=role, project=role.project)
    await repositories.move_project_role_of_related(role=role, target_role=target_role)
    await invitation.arefresh_from_db()
    await membership.arefresh_from_db()
    assert invitation.role_id == target_role.id
    assert membership.role_id == target_role.id


async def test_move_project_role_of_related_ko_role_different_project():
    role = await f.create_project_role()
    target_role = await f.create_project_role()
    with pytest.raises(ex.RoleWithTargetThatDoNotBelong):
        await repositories.move_project_role_of_related(
            role=role, target_role=target_role
        )
