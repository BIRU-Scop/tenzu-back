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
from permissions import (
    check_permissions,
)
from tests.utils import factories as f
from workspaces.memberships.permissions import IsWorkspaceMember


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
