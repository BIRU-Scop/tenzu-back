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
from memberships.permissions import HasPermission
from permissions import (
    check_permissions,
)
from permissions.choices import WorkspacePermissions
from tests.utils import factories as f
from workspaces.memberships.permissions import (
    CanModifyAssociatedRole,
    IsWorkspaceMember,
)


@pytest.mark.django_db()
async def test_check_permission_is_workspace_member():
    user1 = await f.create_user()
    user2 = await f.create_user()
    workspace = await f.create_workspace(name="workspace1", created_by=user1)

    permissions = IsWorkspaceMember()

    # user1 is ws-admin
    assert (
        await check_permissions(permissions=permissions, user=user1, obj=workspace)
        is None
    )
    with pytest.raises(ex.ForbiddenError):
        await check_permissions(permissions=permissions, user=user1, obj=None)
    # user2 isn't ws-admin
    with pytest.raises(ex.ForbiddenError):
        await check_permissions(permissions=permissions, user=user2, obj=workspace)


@pytest.mark.django_db()
async def test_check_permission_has_workspace_permission():
    user1 = await f.create_user()
    user2 = await f.create_user()
    not_member_user = await f.create_user()
    workspace = await f.create_workspace(name="workspace1", created_by=user1)
    ws_role = await f.create_workspace_role(
        permissions=[WorkspacePermissions.MODIFY_WORKSPACE.value],
        is_owner=False,
        workspace=workspace,
    )
    await f.create_workspace_membership(user=user2, workspace=workspace, role=ws_role)

    permissions = HasPermission(WorkspacePermissions.MODIFY_WORKSPACE)

    # user1 is ws-owner
    assert (
        await check_permissions(permissions=permissions, user=user1, obj=workspace)
        is None
    )
    assert user1.workspace_role.slug == "owner"
    user1.workspace_role = None
    # user2 isn't ws-owner but has permission
    assert (
        await check_permissions(permissions=permissions, user=user2, obj=workspace)
        is None
    )
    assert user2.workspace_role == ws_role
    with pytest.raises(ex.ForbiddenError):
        await check_permissions(permissions=permissions, user=user1, obj=None)
    with pytest.raises(ex.ForbiddenError):
        await check_permissions(
            permissions=permissions, user=not_member_user, obj=workspace
        )
    permissions = HasPermission(WorkspacePermissions.CREATE_MODIFY_MEMBER)
    assert (
        await check_permissions(permissions=permissions, user=user1, obj=workspace)
        is None
    )
    assert user1.workspace_role.slug == "owner"
    with pytest.raises(ex.ForbiddenError):
        await check_permissions(permissions=permissions, user=user2, obj=workspace)

    permissions = HasPermission(
        WorkspacePermissions.MODIFY_WORKSPACE, field="workspace"
    )
    assert (
        await check_permissions(permissions=permissions, user=user2, obj=ws_role)
        is None
    )


async def test_check_permission_can_modify_workspaces_membership():
    user1 = f.build_user()
    user2 = f.build_user()
    owner_role = f.build_workspace_role(is_owner=True)
    member_role = f.build_workspace_role(is_owner=False)
    membership1 = f.build_workspace_membership(user=user2, role=owner_role)
    membership2 = f.build_workspace_membership(user=user2, role=member_role)

    permissions = CanModifyAssociatedRole()

    # user is owner
    user1.workspace_role = owner_role
    assert (
        await check_permissions(permissions=permissions, user=user1, obj=membership1)
        is None
    )
    assert (
        await check_permissions(permissions=permissions, user=user1, obj=membership2)
        is None
    )
    # user is not owner
    user1.workspace_role = member_role
    assert (
        await check_permissions(permissions=permissions, user=user1, obj=membership2)
        is None
    )
    with pytest.raises(ex.ForbiddenError):
        await check_permissions(permissions=permissions, user=user1, obj=membership1)
