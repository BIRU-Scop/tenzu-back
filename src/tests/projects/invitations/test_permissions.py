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

from commons.exceptions import api as ex
from permissions import (
    check_permissions,
)
from projects.invitations import permissions
from projects.invitations.permissions import (
    HasPendingProjectInvitation,
    IsProjectInvitationRecipient,
)
from tests.utils import factories as f
from users.models import AnonymousUser

###########################################################################
# check_permissions
###########################################################################


async def test_check_permission_is_projects_invitation_recipient():
    user1 = f.build_user()
    user2 = f.build_user()
    invitation1 = f.build_project_invitation(email=user1.email, user=None)

    permissions = IsProjectInvitationRecipient()

    # user1 is recipient
    assert (
        await check_permissions(permissions=permissions, user=user1, obj=invitation1)
        is None
    )
    # user2 isn't recipient
    with pytest.raises(ex.ForbiddenError):
        await check_permissions(permissions=permissions, user=user2, obj=invitation1)


@pytest.mark.django_db()
async def test_check_permission_has_pending_project_invitation():
    user1 = await f.create_user()
    user2 = await f.create_user()
    invitation = await f.create_project_invitation(email=user1.email, user=user1)

    permissions = HasPendingProjectInvitation()

    # user1 is recipient
    assert (
        await check_permissions(
            permissions=permissions, user=user1, obj=invitation.project
        )
        is None
    )
    # user2 isn't recipient
    with pytest.raises(ex.ForbiddenError):
        await check_permissions(
            permissions=permissions, user=user2, obj=invitation.project
        )
    # project member isn't recipient
    with pytest.raises(ex.ForbiddenError):
        await check_permissions(
            permissions=permissions,
            user=invitation.project.created_by,
            obj=invitation.project,
        )


###########################################################################
# InvitationPermissionsCheck.ANSWER
###########################################################################


@pytest.mark.parametrize(
    "invitation_email, user_email, expected",
    [
        # Allowed / True
        ("test@email.com", "test@email.com", True),
        # Not allowed / False
        ("test1@email.com", "test@email.com", False),
    ],
)
async def test_is_project_invitation_recipient_permission_with_different_emails(
    invitation_email, user_email, expected
):
    perm = permissions.InvitationPermissionsCheck.ANSWER.value
    user = f.build_user(email=invitation_email)
    invitation = f.build_project_invitation(user=user, email=user_email)

    assert await perm.is_authorized(user, invitation) == expected


async def test_is_project_invitation_recipient_permission_with_anonymous_user():
    perm = permissions.InvitationPermissionsCheck.ANSWER.value
    user = AnonymousUser()
    invitation = f.build_project_invitation(user=None, email="some@email.com")

    assert not await perm.is_authorized(user, invitation)
