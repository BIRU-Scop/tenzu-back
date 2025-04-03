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

from tests.utils import factories as f
from workspaces.memberships import repositories
from workspaces.memberships.models import WorkspaceMembership

pytestmark = pytest.mark.django_db(transaction=True)


##########################################################
# create_workspace_memberhip
##########################################################


async def test_create_workspace_membership():
    user = await f.create_user()
    workspace = await f.create_workspace()
    role = workspace.roles.first()

    membership = await repositories.create_workspace_membership(
        user=user, workspace=workspace, role=role
    )

    assert membership.user_id == user.id
    assert membership.workspace_id == workspace.id
    assert membership.role_id == role.id


##########################################################
# list_workspaces_memberships
##########################################################


async def test_list_workspace_memberships():
    admin = await f.create_user()
    user1 = await f.create_user()
    user2 = await f.create_user()
    workspace = await f.create_workspace(created_by=admin)
    role = workspace.roles.first()
    await repositories.create_workspace_membership(
        user=user1, workspace=workspace, role=role
    )
    await repositories.create_workspace_membership(
        user=user2, workspace=workspace, role=role
    )

    memberships = await repositories.list_memberships(
        WorkspaceMembership,
        filters={"workspace_id": workspace.id},
    )
    assert len(memberships) == 3


##########################################################
# get_workspace_membership
##########################################################


async def test_get_workspace_membership():
    user = await f.create_user()
    workspace = await f.create_workspace(created_by=user)

    membership = await repositories.get_membership(
        WorkspaceMembership,
        filters={"user_id": user.id, "workspace_id": workspace.id},
        select_related=["workspace", "user"],
    )
    assert membership.workspace == workspace
    assert membership.user == user

    membership = await repositories.get_membership(
        WorkspaceMembership,
        filters={"id": membership.id},
        select_related=["workspace", "user"],
    )
    assert membership.workspace == workspace
    assert membership.user == user

    membership = await repositories.get_membership(
        WorkspaceMembership,
        filters={"username": user.username},
        select_related=["workspace", "user"],
    )
    assert membership.workspace == workspace
    assert membership.user == user


async def test_get_workspace_membership_none():
    membership = await repositories.get_membership(
        WorkspaceMembership,
        filters={"user_id": uuid.uuid1(), "workspace_id": uuid.uuid1()},
    )
    assert membership is None


##########################################################
# delete workspace memberships
##########################################################


async def test_delete_stories() -> None:
    user = await f.create_user()
    member = await f.create_user()
    workspace = await f.create_workspace(created_by=user)
    role = workspace.roles.first()
    membership = await f.create_workspace_membership(
        workspace=workspace, user=member, role=role
    )
    deleted = await repositories.delete_membership(membership)
    assert deleted == 1


##########################################################
# misc - list_workspace_members
##########################################################


async def test_list_workspace_members():
    admin = await f.create_user()
    user1 = await f.create_user()
    user2 = await f.create_user()
    workspace = await f.create_workspace(created_by=admin)
    role = workspace.roles.first()
    await repositories.create_workspace_membership(
        user=user1, workspace=workspace, role=role
    )
    await repositories.create_workspace_membership(
        user=user2, workspace=workspace, role=role
    )

    list_ws_members = await repositories.list_workspace_members(
        workspace=workspace, exclude_user=admin
    )
    assert len(list_ws_members) == 2
