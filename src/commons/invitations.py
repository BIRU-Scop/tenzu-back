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
from typing import Any, Self

from django.conf import settings

from base.utils.datetime import aware_utcnow
from ninja_jwt.tokens import Token
from projects.invitations.models import ProjectInvitation
from workspaces.invitations.models import WorkspaceInvitation


def is_spam(invitation: ProjectInvitation | WorkspaceInvitation) -> bool:
    last_send_at = (
        invitation.resent_at if invitation.resent_at else invitation.created_at
    )
    time_since_last_send = int(
        (aware_utcnow() - last_send_at).total_seconds() / 60
    )  # in minutes
    return (
        invitation.num_emails_sent
        == settings.INVITATION_RESEND_LIMIT  # max invitations emails already sent
        or time_since_last_send
        < settings.INVITATION_RESEND_TIME  # too soon to send the invitation again
    )


class InvitationToken(Token):
    token_type = "invitation"
    lifetime = settings.GENERAL_INVITATION_LIFETIME
    object_id_field = "id"
    object_id_claim = "invitation_id"

    @property
    def object_id_data(self) -> dict[str, Any]:
        """
        Get the saved object data from the payload.
        """
        key = self.object_id_field
        value = self.payload.get(self.object_id_claim, None)
        return {key: value}

    @classmethod
    async def create_for_object(cls, obj: object) -> Self:
        """
        Returns a token for the given object that will be provided.
        """
        object_id = getattr(obj, cls.object_id_field)
        if not isinstance(object_id, int):
            object_id = str(object_id)
        token = cls()
        token[cls.object_id_claim] = object_id
        return token
