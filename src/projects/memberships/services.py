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

from commons.utils import transaction_atomic_async, transaction_on_commit_async
from memberships import services as memberships_services
from memberships.services import exceptions as ex
from memberships.services import is_membership_the_only_owner  # noqa
from permissions.choices import ProjectPermissions
from projects.invitations import repositories as project_invitations_repositories
from projects.invitations.models import ProjectInvitation
from projects.memberships import events as memberships_events
from projects.memberships import repositories as memberships_repositories
from projects.memberships.models import ProjectMembership, ProjectRole
from projects.projects.models import Project
from stories.assignments import repositories as story_assignments_repositories

##########################################################
# list project memberships
##########################################################


async def list_project_memberships(project: Project) -> list[ProjectMembership]:
    return await memberships_repositories.list_memberships(
        ProjectMembership,
        filters={"project_id": project.id},
        select_related=["user", "role", "project"],
    )


##########################################################
# get project membership
##########################################################


async def get_project_membership(project_id: UUID, username: str) -> ProjectMembership:
    return await memberships_repositories.get_membership(
        ProjectMembership,
        filters={"project_id": project_id, "user__username": username},
        select_related=["user", "role", "project"],
    )


##########################################################
# update
##########################################################


@transaction_atomic_async
async def update_project_membership(
    membership: ProjectMembership, role_slug: str
) -> ProjectMembership:
    try:
        project_role = await memberships_repositories.get_role(
            ProjectRole,
            filters={"project_id": membership.project_id, "slug": role_slug},
        )

    except ProjectRole.DoesNotExist as e:
        raise ex.NonExistingRoleError("Role does not exist") from e

    if not project_role.is_owner:
        if await memberships_services.is_membership_the_only_owner(membership):
            raise ex.MembershipIsTheOnlyOwnerError("Membership is the only owner")

    updated_membership = await memberships_repositories.update_membership(
        membership=membership,
        values={"role": project_role},
    )

    await transaction_on_commit_async(
        memberships_events.emit_event_when_project_membership_is_updated
    )(membership=updated_membership)

    # Check if new role has view_story permission
    view_story_is_deleted = (
        ProjectPermissions.VIEW_STORY.value in membership.role.permissions
        and ProjectPermissions.VIEW_STORY.value not in project_role.permissions
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
    if await memberships_services.is_membership_the_only_owner(membership):
        raise ex.MembershipIsTheOnlyOwnerError("Membership is the only owner")

    deleted = await memberships_repositories.delete_membership(membership)
    if deleted > 0:
        # Delete stories assignments
        await story_assignments_repositories.delete_stories_assignments(
            filters={
                "project_id": membership.project_id,
                "username": membership.user.username,
            }
        )
        # Delete project invitations
        await project_invitations_repositories.delete_invitation(
            ProjectInvitation,
            filters={
                "project_id": membership.project_id,
            },
            q_filter=project_invitations_repositories.username_or_email_query(
                membership.user.email
            ),
        )
        await memberships_events.emit_event_when_project_membership_is_deleted(
            membership=membership
        )
        return True

    return False


##########################################################
# list project roles
##########################################################


async def list_project_roles(project: Project) -> list[ProjectRole]:
    return await memberships_repositories.list_roles(
        ProjectRole, filters={"project_id": project.id}
    )


##########################################################
# get project role
##########################################################


async def get_project_role(project_id: UUID, slug: str) -> ProjectRole:
    return await memberships_repositories.get_role(
        ProjectRole,
        filters={"project_id": project_id, "slug": slug},
        select_related=["project"],
    )


##########################################################
# update project role
##########################################################


@transaction_atomic_async
async def update_project_role_permissions(
    role: ProjectRole, permissions: list[str]
) -> ProjectRole:
    if not role.editable:
        raise ex.NonEditableRoleError(f"Role {role.slug} is not editable")

    project_role_permissions = await memberships_repositories.update_role(
        role=role,
        values={"permissions": permissions},
    )

    await transaction_on_commit_async(
        memberships_events.emit_event_when_project_role_permissions_are_updated
    )(role=role)

    # Check if new permissions have view_story
    view_story_is_deleted = (
        ProjectPermissions.VIEW_STORY.value in role.permissions
        and ProjectPermissions.VIEW_STORY.value not in permissions
    )
    # Unassign stories for user if the new permissions don't have view_story
    if view_story_is_deleted:
        await story_assignments_repositories.delete_stories_assignments(
            filters={"role_id": role.id}
        )

    return project_role_permissions
