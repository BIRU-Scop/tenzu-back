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

from base.utils.datetime import aware_utcnow
from configurations.conf import settings
from projects.invitations.models import ProjectInvitation
from workspaces.invitations.models import WorkspaceInvitation


def is_spam(invitation: ProjectInvitation | WorkspaceInvitation) -> bool:
    last_send_at = invitation.resent_at if invitation.resent_at else invitation.created_at
    time_since_last_send = int((aware_utcnow() - last_send_at).total_seconds() / 60)  # in minutes
    return (
        invitation.num_emails_sent == settings.INVITATION_RESEND_LIMIT  # max invitations emails already sent
        or time_since_last_send < settings.INVITATION_RESEND_TIME  # too soon to send the invitation again
    )
