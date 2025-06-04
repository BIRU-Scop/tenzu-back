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
from typing import cast
from uuid import UUID

from commons.utils import transaction_atomic_async, transaction_on_commit_async
from memberships import services as memberships_services
from memberships.repositories import WorkspaceMembershipAnnotation
from memberships.services import exceptions as ex
from memberships.services import is_membership_the_only_owner  # noqa
from projects.invitations import repositories as project_invitations_repositories
from projects.invitations.models import ProjectInvitation
from projects.memberships.models import ProjectMembership
from projects.projects.models import Project
from stories.assignments import repositories as story_assignments_repositories
from users.models import User
from workspaces.invitations import repositories as workspace_invitations_repositories
from workspaces.invitations.models import WorkspaceInvitation
from workspaces.memberships import events as memberships_events
from workspaces.memberships import repositories as memberships_repositories
from workspaces.memberships.models import WorkspaceMembership, WorkspaceRole
from workspaces.workspaces.models import Workspace

_DEFAULT_WORKSPACE_MEMBERSHIP_ROLE_SLUG = "readonly-member"

##########################################################
# list workspace memberships
##########################################################


async def list_workspace_memberships(
    workspace: Workspace, get_total_projects=False
) -> list[WorkspaceMembership]:
    return await memberships_repositories.list_memberships(
        WorkspaceMembership,
        filters={"workspace_id": workspace.id},
        select_related=["user"],
        annotations={
            "total_projects_is_member": memberships_repositories.TOTAL_PROJECTS_IS_MEMBER_ANNOTATION
        }
        if get_total_projects
        else cast(WorkspaceMembershipAnnotation, {}),
    )


##########################################################
# get workspace membership
##########################################################


async def get_workspace_membership(
    membership_id: UUID, get_total_projects=False
) -> WorkspaceMembership | None:
    return await memberships_repositories.get_membership(
        WorkspaceMembership,
        filters={"id": membership_id},
        select_related=["user", "role", "workspace"],
        annotations={
            "total_projects_is_member": memberships_repositories.TOTAL_PROJECTS_IS_MEMBER_ANNOTATION
        }
        if get_total_projects
        else cast(WorkspaceMembershipAnnotation, {}),
    )


##########################################################
# update workspace membership
##########################################################


async def update_workspace_membership(
    membership: WorkspaceMembership, role_id: UUID, user: User
) -> WorkspaceMembership:
    user_role = getattr(user, "workspace_role", None)

    updated_membership = await memberships_services.update_membership(
        membership=membership, role_id=role_id, user_role=user_role
    )

    await memberships_events.emit_event_when_workspace_membership_is_updated(
        membership=updated_membership
    )

    return updated_membership


##########################################################
# delete workspace membership
##########################################################


async def _handle_membership_succession(
    membership: WorkspaceMembership, user: User, successor_user_id: UUID | None = None
):
    if successor_user_id is not None:
        if successor_user_id == user.id:
            raise ex.SameSuccessorAsCurrentMember(
                "The to-be-deleted member and successor user cannot be the same"
            )
        try:
            successor_membership = await memberships_repositories.get_membership(
                WorkspaceMembership,
                filters={
                    "user_id": successor_user_id,
                    "workspace_id": membership.workspace_id,
                },
                select_related=["user"],
            )
        except WorkspaceMembership.DoesNotExist as e:
            raise ex.MembershipIsTheOnlyOwnerError(
                f"Membership is the only project owner and member {successor_user_id} can't be found in project"
            ) from e
        else:
            await update_workspace_membership(
                successor_membership, membership.role_id, user=user
            )
    else:
        raise ex.MembershipIsTheOnlyOwnerError("Membership is the only workspace owner")


async def _handle_membership_projects_succession(
    membership: WorkspaceMembership, user: User
):
    owner_project_values = [
        pj_values
        async for pj_values in memberships_repositories.only_owner_queryset(
            Project, membership.user, filters={"workspace_id": membership.workspace_id}
        ).values("id", "memberships__role_id")
    ]
    if not owner_project_values:
        return
    if not user.workspace_role.is_owner:
        raise ex.ExistingOwnerProjectMembershipsAndNotOwnerError(
            "Can't delete a user when they are still the only owner of some projects if you're not a workspace owner"
        )
    owner_project_memberships = [
        ProjectMembership(
            user=user,
            project_id=pj_values["id"],
            role_id=pj_values["memberships__role_id"],
        )
        for pj_values in owner_project_values
    ]
    await memberships_repositories.bulk_update_or_create_memberships(
        owner_project_memberships
    )


@transaction_atomic_async
async def _delete_inner_projects_membership(membership: WorkspaceMembership) -> bool:
    deleted = await memberships_repositories.delete_memberships(
        ProjectMembership,
        {
            "project__workspace_id": membership.workspace_id,
            "user_id": membership.user_id,
        },
    )
    if deleted > 0:
        # Delete stories assignments
        await story_assignments_repositories.delete_stories_assignments(
            filters={
                "story__project__workspace_id": membership.workspace_id,
                "user_id": membership.user_id,
            }
        )
        # Delete project invitations
        await project_invitations_repositories.delete_invitation(
            ProjectInvitation,
            filters={
                "project__workspace_id": membership.workspace_id,
            },
            q_filter=project_invitations_repositories.invitation_username_or_email_query(
                membership.user.email
            ),
        )
        return True

    return False


@transaction_atomic_async
async def delete_workspace_membership(
    membership: WorkspaceMembership, user: User, successor_user_id: UUID | None = None
) -> bool:
    if await memberships_services.is_membership_the_only_owner(membership):
        await _handle_membership_succession(membership, user, successor_user_id)
    if user.id == membership.user_id:
        # user is deleting themself
        if await memberships_repositories.exists_membership(
            ProjectMembership,
            filters={
                "user": membership.user,
                "project__workspace_id": membership.workspace_id,
            },
        ):
            raise ex.ExistingProjectMembershipsError(
                "You can't delete this workspace membership while the user is still a member of some projects"
            )
    else:
        # user is deleting someone else
        await _handle_membership_projects_succession(membership, user)

    await _delete_inner_projects_membership(membership)
    deleted = await memberships_repositories.delete_memberships(
        WorkspaceMembership, {"id": membership.id}
    )
    if deleted > 0:
        # Delete workspace invitations
        await workspace_invitations_repositories.delete_invitation(
            WorkspaceInvitation,
            filters={
                "workspace_id": membership.workspace_id,
            },
            q_filter=workspace_invitations_repositories.invitation_username_or_email_query(
                membership.user.email
            ),
        )
        await transaction_on_commit_async(
            memberships_events.emit_event_when_workspace_membership_is_deleted
        )(membership=membership)
        return True

    return False


##########################################################
# misc workspace membership
##########################################################


async def create_default_workspace_membership(workspace_id: UUID, user: User):
    role = await get_workspace_role(
        workspace_id, _DEFAULT_WORKSPACE_MEMBERSHIP_ROLE_SLUG
    )
    await memberships_repositories.create_workspace_membership(
        workspace=role.workspace, role=role, user=user
    )


##########################################################
# list workspace roles
##########################################################


async def list_workspace_roles(workspace: Workspace) -> list[WorkspaceRole]:
    return await memberships_repositories.list_roles(
        WorkspaceRole, filters={"workspace_id": workspace.id}, get_total_members=True
    )


##########################################################
# get workspace role
##########################################################


async def get_workspace_role(workspace_id: UUID, slug: str) -> WorkspaceRole:
    return await memberships_repositories.get_role(
        WorkspaceRole,
        filters={"workspace_id": workspace_id, "slug": slug},
        select_related=["workspace"],
    )
