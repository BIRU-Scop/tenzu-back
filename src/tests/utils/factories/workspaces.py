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

from asgiref.sync import sync_to_async

from memberships.choices import InvitationStatus
from permissions import choices

from .base import Factory, factory

# WORKSPACE ROLE


class WorkspaceRoleFactory(Factory):
    name = factory.Sequence(lambda n: f"Role {n}")
    slug = factory.Sequence(lambda n: f"test-role-{n}")
    permissions = choices.WorkspacePermissions.values
    workspace = factory.SubFactory("tests.utils.factories.WorkspaceFactory")

    class Meta:
        model = "workspaces_memberships.WorkspaceRole"


@sync_to_async
def create_workspace_role(**kwargs):
    return WorkspaceRoleFactory.create(**kwargs)


def build_workspace_role(**kwargs):
    return WorkspaceRoleFactory.build(**kwargs)


# WORKSPACE MEMBERSHIP


class WorkspaceMembershipFactory(Factory):
    user = factory.SubFactory("tests.utils.factories.UserFactory")
    workspace = factory.SubFactory("tests.utils.factories.WorkspaceFactory")
    role = factory.SubFactory("tests.utils.factories.WorkspaceRoleFactory")

    class Meta:
        model = "workspaces_memberships.WorkspaceMembership"


@sync_to_async
def create_workspace_membership(**kwargs):
    return WorkspaceMembershipFactory.create(**kwargs)


def build_workspace_membership(**kwargs):
    return WorkspaceMembershipFactory.build(**kwargs)


# WORKSPACE INVITATION


class WorkspaceInvitationFactory(Factory):
    status = InvitationStatus.PENDING
    email = factory.Sequence(lambda n: f"user{n}@email.com")
    user = factory.SubFactory("tests.utils.factories.UserFactory")
    workspace = factory.SubFactory("tests.utils.factories.WorkspaceFactory")
    role = factory.SubFactory("tests.utils.factories.WorkspaceRoleFactory")
    invited_by = factory.SubFactory("tests.utils.factories.UserFactory")

    class Meta:
        model = "workspaces_invitations.WorkspaceInvitation"


@sync_to_async
def create_workspace_invitation(**kwargs):
    return WorkspaceInvitationFactory.create(**kwargs)


def build_workspace_invitation(**kwargs):
    return WorkspaceInvitationFactory.build(**kwargs)


# WORKSPACE


class WorkspaceFactory(Factory):
    name = factory.Sequence(lambda n: f"workspace {n}")
    created_by = factory.SubFactory("tests.utils.factories.UserFactory")

    class Meta:
        model = "workspaces.Workspace"


@sync_to_async
def create_workspace(**kwargs):
    """Create workspace and its dependencies"""
    workspace = WorkspaceFactory.create(**kwargs)

    owner_role = WorkspaceRoleFactory.create(
        workspace=workspace, is_owner=True, slug="owner"
    )
    WorkspaceMembershipFactory.create(
        user=workspace.created_by, workspace=workspace, role=owner_role
    )

    return workspace


def build_workspace(**kwargs):
    return WorkspaceFactory.build(**kwargs)
