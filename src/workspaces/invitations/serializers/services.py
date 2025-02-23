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

from workspaces.invitations.models import WorkspaceInvitation
from workspaces.invitations.serializers import (
    CreateWorkspaceInvitationsSerializer,
    PublicWorkspaceInvitationSerializer,
)


def serialize_create_workspace_invitations(
    invitations: list[WorkspaceInvitation],
    already_members: int,
) -> CreateWorkspaceInvitationsSerializer:
    return CreateWorkspaceInvitationsSerializer(
        invitations=invitations, already_members=already_members
    )


def serialize_public_workspace_invitation(
    invitation: WorkspaceInvitation,
    available_logins: list[str],
) -> PublicWorkspaceInvitationSerializer:
    return PublicWorkspaceInvitationSerializer(
        status=invitation.status,
        email=invitation.email,
        existing_user=invitation.user is not None,
        available_logins=available_logins,
        workspace=invitation.workspace,
    )
