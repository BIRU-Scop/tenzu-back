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

from uuid import UUID

from projects.invitations import repositories as project_invitations_repositories
from projects.memberships import events as memberships_events
from projects.memberships import repositories as memberships_repositories
from projects.memberships.models import ProjectMembership
from projects.memberships.services import exceptions as ex
from projects.projects.models import Project
from projects.roles import repositories as pj_roles_repositories
from projects.roles.models import ProjectRole
from stories.assignments import repositories as story_assignments_repositories
from stories.stories import permissions as stories_permissions

##########################################################
# list project memberships
##########################################################


async def list_project_memberships(project: Project) -> list[ProjectMembership]:
    return await memberships_repositories.list_project_memberships(
        filters={"project_id": project.id},
        select_related=["user", "role", "project"],
    )


##########################################################
# get project membership
##########################################################


async def get_project_membership(
    project_id: UUID, username: str
) -> ProjectMembership | None:
    return await memberships_repositories.get_project_membership(
        filters={"project_id": project_id, "username": username},
        select_related=["user", "role", "project", "workspace"],
    )


##########################################################
# update
##########################################################


async def update_project_membership(
    membership: ProjectMembership, role_slug: str
) -> ProjectMembership:
    project_role = await pj_roles_repositories.get_project_role(
        filters={"project_id": membership.project_id, "slug": role_slug}
    )

    if not project_role:
        raise ex.NonExistingRoleError("Role does not exist")

    if not project_role.is_admin:
        if await _is_membership_the_only_admin(membership_role=membership.role):
            raise ex.MembershipIsTheOnlyAdminError("Membership is the only admin")

    # Check if new role has view_story permission
    view_story_is_deleted = False
    if membership.role.permissions:
        view_story_is_deleted = (
            await stories_permissions.is_view_story_permission_deleted(
                old_permissions=membership.role.permissions,
                new_permissions=project_role.permissions,
            )
        )

    updated_membership = await memberships_repositories.update_project_membership(
        membership=membership,
        values={"role": project_role},
    )

    await memberships_events.emit_event_when_project_membership_is_updated(
        membership=updated_membership
    )

    # Unassign stories for user if the new role doesn't have view_story permission
    if view_story_is_deleted:
        await story_assignments_repositories.delete_stories_assignments(
            filters={
                "project_id": membership.project_id,
                "username": membership.user.username,
            }
        )

    return updated_membership


##########################################################
# delete project membership
##########################################################


async def delete_project_membership(
    membership: ProjectMembership,
) -> bool:
    if await _is_membership_the_only_admin(membership_role=membership.role):
        raise ex.MembershipIsTheOnlyAdminError("Membership is the only admin")

    deleted = await memberships_repositories.delete_project_membership(
        filters={"id": membership.id},
    )
    if deleted > 0:
        # Delete stories assignments
        await story_assignments_repositories.delete_stories_assignments(
            filters={
                "project_id": membership.project_id,
                "username": membership.user.username,
            }
        )
        # Delete project invitations
        await project_invitations_repositories.delete_project_invitation(
            filters={
                "project_id": membership.project_id,
                "username_or_email": membership.user.email,
            },
        )
        await memberships_events.emit_event_when_project_membership_is_deleted(
            membership=membership
        )
        return True

    return False


##########################################################
# misc
##########################################################


async def _is_membership_the_only_admin(membership_role: ProjectRole) -> bool:
    if not membership_role.is_admin:
        return False

    num_admins = await memberships_repositories.get_total_project_memberships(
        filters={"role_id": membership_role.id}
    )
    return num_admins == 1
