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
from typing import Any
from uuid import UUID

from django.db.models import RestrictedError

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
from users.models import User

##########################################################
# list project memberships
##########################################################


async def list_project_memberships(project: Project) -> list[ProjectMembership]:
    return await memberships_repositories.list_memberships(
        ProjectMembership,
        filters={"project_id": project.id},
        select_related=["user"],
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
    membership: ProjectMembership, role_id: UUID, user: User
) -> ProjectMembership:
    user_role = user.project_role

    updated_membership = await memberships_services.update_membership(
        membership=membership, role_id=role_id, user_role=user_role
    )

    await transaction_on_commit_async(
        memberships_events.emit_event_when_project_membership_is_updated
    )(membership=updated_membership)

    # Check if new role has view_story permission
    view_story_is_deleted = (
        ProjectPermissions.VIEW_STORY.value in membership.role.permissions
        and ProjectPermissions.VIEW_STORY.value
        not in updated_membership.role.permissions
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


@transaction_atomic_async
async def delete_project_membership(
    membership: ProjectMembership,
) -> bool:
    if await memberships_services.is_membership_the_only_owner(membership):
        raise ex.MembershipIsTheOnlyOwnerError("Membership is the only project owner")

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
            q_filter=project_invitations_repositories.invitation_username_or_email_query(
                membership.user.email
            ),
        )
        await transaction_on_commit_async(
            memberships_events.emit_event_when_project_membership_is_deleted
        )(membership=membership)
        return True

    return False


##########################################################
# list project roles
##########################################################


async def list_project_roles(project: Project) -> list[ProjectRole]:
    return await memberships_repositories.list_roles(
        ProjectRole, filters={"project_id": project.id}, get_total_members=True
    )


##########################################################
# get project role
##########################################################


async def get_project_role(role_id: UUID) -> ProjectRole:
    return await memberships_repositories.get_role(
        ProjectRole,
        filters={"id": role_id},
        select_related=["project"],
    )


##########################################################
# create project role
##########################################################


@transaction_atomic_async
async def create_project_role(
    name: str, permissions: list[str], project_id: UUID
) -> ProjectRole:
    role = await memberships_repositories.create_project_role(
        name=name,
        permissions=permissions,
        project_id=project_id,
    )

    # Emit event
    await transaction_on_commit_async(
        memberships_events.emit_event_when_project_role_is_created
    )(role=role)

    return role


##########################################################
# update project role
##########################################################


@transaction_atomic_async
async def update_project_role(
    role: ProjectRole, values: dict[str, Any] = {}
) -> ProjectRole:
    if not role.editable:
        raise ex.NonEditableRoleError(f"Role {role.slug} is not editable")

    updated_role = await memberships_repositories.update_role(
        role=role,
        values=values,
    )

    await transaction_on_commit_async(
        memberships_events.emit_event_when_project_role_is_updated
    )(role=role)

    if "permissions" in values:
        # Check if new permissions have view_story
        view_story_is_deleted = (
            ProjectPermissions.VIEW_STORY.value in role.permissions
            and ProjectPermissions.VIEW_STORY.value not in values["permissions"]
        )
        # Unassign stories for user if the new permissions don't have view_story
        if view_story_is_deleted:
            await story_assignments_repositories.delete_stories_assignments(
                filters={"role_id": role.id}
            )

    return updated_role


##########################################################
# delete project role
##########################################################


@transaction_atomic_async
async def delete_project_role(
    user: User,
    role: ProjectRole,
    target_role_id: UUID | None = None,
) -> bool:
    if not role.editable:
        raise ex.NonEditableRoleError(f"Role {role.slug} is not editable")
    target_role = None
    if target_role_id is not None:
        try:
            target_role = await get_project_role(role_id=target_role_id)
        except ProjectRole.DoesNotExist as e:
            raise ex.NonExistingMoveToRole(
                f"The role '{target_role_id}' doesn't exist"
            ) from e
        if target_role.project_id != role.project_id:
            raise ex.NonExistingMoveToRole(
                f"The role '{target_role_id}' is in a different project"
            )
        if target_role.id == role.id:
            raise ex.SameMoveToRole(
                "The to-be-deleted role and the target-role cannot be the same"
            )
        if not user.project_role.is_owner and target_role.is_owner:
            raise ex.OwnerRoleNotAuthorisedError(
                "You don't have the permissions to promote existing memberships or invitations to owner"
            )

        await memberships_repositories.move_project_role_of_related(
            role=role, target_role=target_role
        )
    try:
        deleted = await transaction_atomic_async(
            memberships_repositories.delete_project_role
        )(
            role=role,
        )
    except RestrictedError:
        # TODO handle concurrency issue where target_role_id was provided
        #  but a membership or invitation was created in the meantime
        raise ex.RequiredMoveToRole(
            "Some memberships or invitations use this role, you need to provide a role then can use instead"
        )

    if deleted > 0:
        await transaction_on_commit_async(
            memberships_events.emit_event_when_project_role_is_deleted
        )(role=role, target_role=target_role)
        return True
    return False
