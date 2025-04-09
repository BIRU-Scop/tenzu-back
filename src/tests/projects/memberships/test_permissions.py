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

from commons.exceptions import api as ex
from memberships.permissions import CanModifyAssociatedRole, HasPermission, IsMember
from permissions import (
    check_permissions,
)
from permissions.choices import ProjectPermissions
from tests.utils import factories as f


@pytest.mark.django_db()
async def test_check_permission_is_project_member(project_template):
    user1 = await f.create_user()
    user2 = await f.create_user()
    project = await f.create_project(
        project_template, name="project1", created_by=user1
    )

    permissions = IsMember("project")

    # user1 is ws-admin
    assert (
        await check_permissions(permissions=permissions, user=user1, obj=project)
        is None
    )
    with pytest.raises(ex.ForbiddenError):
        await check_permissions(permissions=permissions, user=user1, obj=None)
    # user2 isn't ws-admin
    with pytest.raises(ex.ForbiddenError):
        await check_permissions(permissions=permissions, user=user2, obj=project)
    # wrong object
    permissions = IsMember("workspace")
    with pytest.raises(ValueError):
        await check_permissions(permissions=permissions, user=user1, obj=project)


@pytest.mark.django_db()
async def test_check_permission_has_project_permission(project_template):
    user1 = await f.create_user()
    user2 = await f.create_user()
    not_member_user = await f.create_user()
    project = await f.create_project(
        project_template, name="project1", created_by=user1
    )
    pj_role = await f.create_project_role(
        permissions=[ProjectPermissions.VIEW_STORY.value],
        is_owner=False,
        project=project,
    )
    await f.create_project_membership(user=user2, project=project, role=pj_role)

    permissions = HasPermission("project", ProjectPermissions.VIEW_STORY)

    # user1 is pj-owner
    assert (
        await check_permissions(permissions=permissions, user=user1, obj=project)
        is None
    )
    assert user1.project_role.is_owner
    user1.project_role = None
    # user2 isn't pj-owner but has permission
    assert (
        await check_permissions(permissions=permissions, user=user2, obj=project)
        is None
    )
    assert user2.project_role == pj_role
    # error cases
    # empty obj
    with pytest.raises(ex.ForbiddenError):
        await check_permissions(permissions=permissions, user=user1, obj=None)
    # not a member
    with pytest.raises(ex.ForbiddenError):
        await check_permissions(
            permissions=permissions, user=not_member_user, obj=project
        )
    # wrong model
    permissions = HasPermission("workspace", ProjectPermissions.VIEW_STORY)
    with pytest.raises(ValueError):
        await check_permissions(permissions=permissions, user=user2, obj=project)

    permissions = HasPermission("project", ProjectPermissions.CREATE_STORY)
    # user1 is pj-owner
    assert (
        await check_permissions(permissions=permissions, user=user1, obj=project)
        is None
    )
    assert user1.project_role.is_owner
    # user2 isn't pj-owner and doesn't have permission
    with pytest.raises(ex.ForbiddenError):
        await check_permissions(permissions=permissions, user=user2, obj=project)

    # check on related model
    permissions = HasPermission(
        "project", ProjectPermissions.VIEW_STORY, field="project"
    )
    assert (
        await check_permissions(permissions=permissions, user=user2, obj=pj_role)
        is None
    )


async def test_check_permission_can_modify_projects_membership():
    user1 = f.build_user()
    user2 = f.build_user()
    owner_role = f.build_project_role(is_owner=True)
    member_role = f.build_project_role(is_owner=False)
    membership1 = f.build_project_membership(user=user2, role=owner_role)
    membership2 = f.build_project_membership(user=user2, role=member_role)

    permissions = CanModifyAssociatedRole("project")

    # user is owner
    user1.project_role = owner_role
    assert (
        await check_permissions(permissions=permissions, user=user1, obj=membership1)
        is None
    )
    assert (
        await check_permissions(permissions=permissions, user=user1, obj=membership2)
        is None
    )
    # user is not owner
    user1.project_role = member_role
    assert (
        await check_permissions(permissions=permissions, user=user1, obj=membership2)
        is None
    )
    with pytest.raises(ex.ForbiddenError):
        await check_permissions(permissions=permissions, user=user1, obj=membership1)
