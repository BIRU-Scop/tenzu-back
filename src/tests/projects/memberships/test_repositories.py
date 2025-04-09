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
from tests.utils import factories as f

pytestmark = pytest.mark.django_db


##########################################################
# create_project_membership
##########################################################


async def test_create_project_membership(project_template):
    user = await f.create_user()
    project = await f.create_project(project_template)
    role = await f.create_project_role(project=project)
    membership = await repositories.create_project_membership(
        user=user, project=project, role=role
    )
    memberships = [m async for m in project.memberships.all()]
    assert membership in memberships


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
    await repositories.create_project_membership(user=user1, project=project, role=role)
    await repositories.create_project_membership(user=user2, project=project, role=role)

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
    membership = await repositories.create_project_membership(
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
    membership = await repositories.create_project_membership(
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
    project = await f.create_project(project_template)
    user = await f.create_user()
    role = await f.create_project_role(project=project)
    membership = await repositories.create_project_membership(
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

    await repositories.create_project_membership(user=user, project=project, role=role)
    assert not await repositories.has_other_owner_memberships(owner_membership)

    await repositories.create_project_membership(
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

    await repositories.create_project_membership(user=user, project=project, role=role)

    project_member = await repositories.list_members(reference_object=project)
    assert len(project_member) == 2

    project_member = await repositories.list_members(
        reference_object=project, exclude_user=user
    )
    assert len(project_member) == 1


##########################################################
# create_project_roles
##########################################################


async def test_create_project_roles(project_template):
    project = await f.create_project(project_template)
    project_role_res = await repositories.create_project_role(
        name="project-role",
        order=1,
        project=project,
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
    await repositories.create_project_membership(user=user, project=project, role=role)

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
