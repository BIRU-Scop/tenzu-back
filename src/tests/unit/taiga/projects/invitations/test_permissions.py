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

from projects.invitations import permissions
from tests.utils import factories as f
from users.models import AnonymousUser

###########################################################################
# IsProjectInvitationRecipient
###########################################################################


@pytest.mark.parametrize(
    "invitation_email, user_email, user_is_active, expected",
    [
        # Allowed / True
        ("test@email.com", "test@email.com", True, True),
        # Not allowed / False
        ("test@email.com", "test@email.com", False, False),
        ("test1@email.com", "test@email.com", True, False),
    ],
)
async def test_is_project_invitation_recipient_permission_with_different_emails(
    invitation_email, user_email, user_is_active, expected
):
    perm = permissions.IsAuthenticatedProjectInvitationRecipient()
    user = f.build_user(email=invitation_email, is_active=user_is_active)
    invitation = f.build_project_invitation(user=user, email=user_email)

    assert await perm.is_authorized(user, invitation) == expected


async def test_is_project_invitation_recipient_permission_with_anonymous_user():
    perm = permissions.IsAuthenticatedProjectInvitationRecipient()
    user = AnonymousUser()
    invitation = f.build_project_invitation(user=None, email="some@email.com")

    assert not await perm.is_authorized(user, invitation)
