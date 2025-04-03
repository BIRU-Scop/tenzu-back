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

from typing import Final
from uuid import UUID

from base.api import Pagination
from projects.memberships import repositories as projects_memberships_repositories
from projects.memberships.models import ProjectMembership
from projects.projects import repositories as projects_repositories
from users import repositories as users_repositories
from workspaces.invitations import repositories as workspace_invitations_repositories
from workspaces.memberships import events as workspace_memberships_events
from workspaces.memberships import repositories as workspace_memberships_repositories
from workspaces.memberships.models import WorkspaceMembership
from workspaces.memberships.serializers import (
    WorkspaceGuestDetailSerializer,
    WorkspaceMembershipDetailSerializer,
)
from workspaces.memberships.serializers import services as serializer_services
from workspaces.memberships.services import exceptions as ex
from workspaces.workspaces.models import Workspace

##########################################################
# list workspace memberships
##########################################################


async def list_workspace_memberships(
    workspace: Workspace,
) -> list[WorkspaceMembershipDetailSerializer]:
    ws_memberships = (
        await workspace_memberships_repositories.list_workspace_memberships(
            filters={"workspace_id": workspace.id},
            select_related=["user", "workspace"],
        )
    )
    return [
        serializer_services.serialize_workspace_membership_detail(
            ws_membership=ws_membership,
            projects=await projects_repositories.list_projects(
                filters={
                    "workspace_id": ws_membership.workspace_id,
                    "memberships__user_id": ws_membership.user_id,
                },
            ),
        )
        for ws_membership in ws_memberships
    ]


##########################################################
# list workspace guests
##########################################################


async def list_paginated_workspace_guests(
    workspace: Workspace, offset: int, limit: int
) -> tuple[Pagination, list[WorkspaceGuestDetailSerializer]]:
    ws_guests = await users_repositories.list_users(
        filters={"guests_in_workspace": workspace},
        offset=offset,
        limit=limit,
    )
    pagination = Pagination(offset=offset, limit=limit)
    serialized_guests = [
        serializer_services.serialize_workspace_guest_detail(
            user=ws_guest,
            projects=await projects_repositories.list_projects(
                filters={
                    "workspace_id": workspace.id,
                    "memberships__user_id": ws_guest.id,
                },
            ),
        )
        for ws_guest in ws_guests
    ]

    return pagination, serialized_guests


##########################################################
# get workspace membership
##########################################################


async def get_workspace_membership(
    workspace_id: UUID,
    username: str,
) -> WorkspaceMembership | None:
    return await workspace_memberships_repositories.get_workspace_membership(
        filters={"workspace_id": workspace_id, "username": username},
        select_related=["workspace", "user"],
    )


##########################################################
# delete workspace membership
##########################################################


async def delete_workspace_membership(
    membership: WorkspaceMembership,
) -> bool:
    workspace_total_members = (
        await workspace_memberships_repositories.get_total_workspace_memberships(
            filters={"workspace_id": membership.workspace_id},
        )
    )
    if workspace_total_members == 1:
        raise ex.MembershipIsTheOnlyMemberError("Membership is the only member")

    deleted = await workspace_memberships_repositories.delete_workspace_memberships(
        filters={"id": membership.id},
    )
    if deleted > 0:
        # Delete workspace invitations
        await workspace_invitations_repositories.delete_workspace_invitation(
            filters={
                "workspace_id": membership.workspace_id,
            },
            q_filter=workspace_invitations_repositories.username_or_email_query(
                membership.user.email
            ),
        )
        await workspace_memberships_events.emit_event_when_workspace_membership_is_deleted(
            membership=membership
        )
        return True

    return False


##########################################################
# misc
##########################################################

WS_ROLE_NAME_MEMBER: Final = "member"
WS_ROLE_NAME_GUEST: Final = "guest"
WS_ROLE_NAME_NONE: Final = "none"


async def get_workspace_role_name(
    workspace_id: UUID,
    user_id: UUID | None,
) -> str:
    if not user_id:
        return WS_ROLE_NAME_NONE
    try:
        if await workspace_memberships_repositories.get_workspace_membership(
            filters={"workspace_id": workspace_id, "user_id": user_id},
        ):
            return WS_ROLE_NAME_MEMBER
        elif await projects_memberships_repositories.get_membership(
            ProjectMembership,
            filters={"user_id": user_id, "project__workspace_id": workspace_id},
        ):
            return WS_ROLE_NAME_GUEST
    except ProjectMembership.DoesNotExist:
        pass
    return WS_ROLE_NAME_NONE
