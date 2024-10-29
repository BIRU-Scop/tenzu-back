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

from projects.memberships import repositories
from projects.memberships.models import ProjectMembership
from projects.projects.models import Project
from tests.utils import factories as f

pytestmark = pytest.mark.django_db


##########################################################
# create_project_membership
##########################################################


@sync_to_async
def _get_memberships(project: Project) -> list[ProjectMembership]:
    return list(project.memberships.all())


async def test_create_project_membership():
    user = await f.create_user()
    project = await f.create_project()
    role = await f.create_project_role(project=project)
    membership = await repositories.create_project_membership(user=user, project=project, role=role)
    memberships = await _get_memberships(project=project)
    assert membership in memberships


##########################################################
# list_project_memberships
##########################################################


async def test_list_project_memberships():
    admin = await f.create_user()
    user1 = await f.create_user()
    user2 = await f.create_user()
    project = await f.create_project(created_by=admin)
    role = await f.create_project_role(project=project)
    await repositories.create_project_membership(user=user1, project=project, role=role)
    await repositories.create_project_membership(user=user2, project=project, role=role)

    memberships = await repositories.list_project_memberships(filters={"project_id": project.id})
    assert len(memberships) == 3


##########################################################
# get_project_membership
##########################################################


async def test_get_project_membership():
    user = await f.create_user()
    project = await f.create_project()
    role = await f.create_project_role(project=project)
    membership = await repositories.create_project_membership(user=user, project=project, role=role)

    ret_membership = repositories.get_project_membership(filters={"project_id": project.id, "username": user.username})
    assert await ret_membership == membership


##########################################################
# update_project_membership
##########################################################


async def test_update_project_membership():
    user = await f.create_user()
    project = await f.create_project()
    role = await f.create_project_role(project=project)
    membership = await repositories.create_project_membership(user=user, project=project, role=role)

    new_role = await f.create_project_role(project=project)
    updated_membership = await repositories.update_project_membership(membership=membership, values={"role": new_role})
    assert updated_membership.role == new_role


##########################################################
# delete_project_membership
##########################################################


async def test_delete_project_membership() -> None:
    project = await f.create_project()
    user = await f.create_user()
    role = await f.create_project_role(project=project)
    membership = await repositories.create_project_membership(user=user, project=project, role=role)
    deleted = await repositories.delete_project_membership(
        filters={"id": membership.id},
    )
    assert deleted == 1


##########################################################
# misc - list_project_members
##########################################################


async def test_list_project_members():
    user = await f.create_user()
    project = await f.create_project()
    role = await f.create_project_role(project=project)

    project_member = await repositories.list_project_members(project=project)
    assert len(project_member) == 1

    await repositories.create_project_membership(user=user, project=project, role=role)

    project_member = await repositories.list_project_members(project=project)
    assert len(project_member) == 2


##########################################################
# misc - list_project_members_excluding_user
##########################################################


async def test_list_project_members_excluding_user():
    admin = await f.create_user()
    user1 = await f.create_user()
    user2 = await f.create_user()
    project = await f.create_project(created_by=admin)
    role = await f.create_project_role(project=project)
    await repositories.create_project_membership(user=user1, project=project, role=role)
    await repositories.create_project_membership(user=user2, project=project, role=role)

    list_pj_members = await repositories.list_project_members_excluding_user(project=project, exclude_user=admin)
    assert len(list_pj_members) == 2


##########################################################
# misc - get_total_project_memberships
##########################################################


async def test_get_total_project_memberships():
    admin = await f.create_user()
    user1 = await f.create_user()
    user2 = await f.create_user()
    project = await f.create_project(created_by=admin)
    role = await f.create_project_role(project=project)
    await repositories.create_project_membership(user=user1, project=project, role=role)
    await repositories.create_project_membership(user=user2, project=project, role=role)

    total_memberships = await repositories.get_total_project_memberships(filters={"project_id": project.id})
    assert total_memberships == 3


##########################################################
# misc - exist_project_membership
##########################################################


async def test_exist_project_membership():
    admin = await f.create_user()
    user1 = await f.create_user()
    user2 = await f.create_user()
    project = await f.create_project(created_by=admin)
    role = await f.create_project_role(project=project)
    await repositories.create_project_membership(user=user1, project=project, role=role)

    admin_is_member = await repositories.exist_project_membership(
        filters={"project_id": project.id, "user_id": admin.id}
    )
    user1_is_member = await repositories.exist_project_membership(
        filters={"project_id": project.id, "user_id": user1.id}
    )
    user2_is_member = await repositories.exist_project_membership(
        filters={"project_id": project.id, "user_id": user2.id}
    )

    assert admin_is_member is True
    assert user1_is_member is True
    assert user2_is_member is False
