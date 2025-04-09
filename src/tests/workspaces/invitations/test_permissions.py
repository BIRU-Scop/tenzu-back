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
from memberships.permissions import (
    CanModifyAssociatedRole,
    HasPendingInvitation,
    IsInvitationRecipient,
)
from permissions import (
    check_permissions,
)
from tests.utils import factories as f

###########################################################################
# check_permissions
###########################################################################


async def test_check_permission_is_workspaces_invitation_recipient():
    user1 = f.build_user()
    user2 = f.build_user()
    invitation1 = f.build_workspace_invitation(email=user1.email, user=None)

    permissions = IsInvitationRecipient()

    # user1 is recipient
    assert (
        await check_permissions(permissions=permissions, user=user1, obj=invitation1)
        is None
    )
    # user2 isn't recipient
    with pytest.raises(ex.ForbiddenError):
        await check_permissions(permissions=permissions, user=user2, obj=invitation1)


@pytest.mark.django_db()
async def test_check_permission_has_pending_workspace_invitation():
    user1 = await f.create_user()
    user2 = await f.create_user()
    invitation = await f.create_workspace_invitation(email=user1.email, user=user1)

    permissions = HasPendingInvitation()

    # user1 is recipient
    assert (
        await check_permissions(
            permissions=permissions, user=user1, obj=invitation.workspace
        )
        is None
    )
    # user2 isn't recipient
    with pytest.raises(ex.ForbiddenError):
        await check_permissions(
            permissions=permissions, user=user2, obj=invitation.workspace
        )
    # workspace member isn't recipient
    with pytest.raises(ex.ForbiddenError):
        await check_permissions(
            permissions=permissions,
            user=invitation.workspace.created_by,
            obj=invitation.workspace,
        )


async def test_check_permission_can_modify_workspaces_invitation():
    user = f.build_user()
    owner_role = f.build_workspace_role(is_owner=True)
    member_role = f.build_workspace_role(is_owner=False)
    invitation1 = f.build_workspace_invitation(
        email="test@demo.test", user=None, role=owner_role
    )
    invitation2 = f.build_workspace_invitation(
        email="test@demo.test", user=None, role=member_role
    )

    permissions = CanModifyAssociatedRole("workspace")

    # user is owner
    user.workspace_role = owner_role
    assert (
        await check_permissions(permissions=permissions, user=user, obj=invitation1)
        is None
    )
    assert (
        await check_permissions(permissions=permissions, user=user, obj=invitation2)
        is None
    )
    # user is not owner
    user.workspace_role = member_role
    assert (
        await check_permissions(permissions=permissions, user=user, obj=invitation2)
        is None
    )
    with pytest.raises(ex.ForbiddenError):
        await check_permissions(permissions=permissions, user=user, obj=invitation1)
