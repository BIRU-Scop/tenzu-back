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

from permissions import choices
from projects.projects import repositories as projects_repositories

from .base import Factory, factory

# PROJECT ROLE


class ProjectRoleFactory(Factory):
    name = factory.Sequence(lambda n: f"Role {n}")
    slug = factory.Sequence(lambda n: f"test-role-{n}")
    permissions = choices.ProjectPermissions.values
    project = factory.SubFactory("tests.utils.factories.ProjectFactory")

    class Meta:
        model = "projects_roles.ProjectRole"


@sync_to_async
def create_project_role(**kwargs):
    return ProjectRoleFactory.create(**kwargs)


def build_project_role(**kwargs):
    return ProjectRoleFactory.build(**kwargs)


# PROJECT MEMBERSHIP


class ProjectMembershipFactory(Factory):
    user = factory.SubFactory("tests.utils.factories.UserFactory")
    project = factory.SubFactory("tests.utils.factories.ProjectFactory")
    role = factory.SubFactory("tests.utils.factories.ProjectRoleFactory")

    class Meta:
        model = "projects_memberships.ProjectMembership"


@sync_to_async
def create_project_membership(**kwargs):
    return ProjectMembershipFactory.create(**kwargs)


def build_project_membership(**kwargs):
    return ProjectMembershipFactory.build(**kwargs)


# PROJECT INVITATION


class ProjectInvitationFactory(Factory):
    email = factory.Sequence(lambda n: f"user{n}@email.com")
    user = factory.SubFactory("tests.utils.factories.UserFactory")
    project = factory.SubFactory("tests.utils.factories.ProjectFactory")
    role = factory.SubFactory("tests.utils.factories.ProjectRoleFactory")
    invited_by = factory.SubFactory("tests.utils.factories.UserFactory")

    class Meta:
        model = "projects_invitations.ProjectInvitation"


@sync_to_async
def create_project_invitation(**kwargs):
    return ProjectInvitationFactory.create(**kwargs)


def build_project_invitation(**kwargs):
    return ProjectInvitationFactory.build(**kwargs)


# PROJECT


class ProjectFactory(Factory):
    name = factory.Sequence(lambda n: f"Project {n}")
    description = factory.Sequence(lambda n: f"Description {n}")
    created_by = factory.SubFactory("tests.utils.factories.UserFactory")
    workspace = factory.SubFactory("tests.utils.factories.WorkspaceFactory")

    class Meta:
        model = "projects.Project"


@sync_to_async
def create_simple_project(**kwargs):
    return ProjectFactory.create(**kwargs)


@sync_to_async
def create_project(template, **kwargs):
    """Create project and its dependencies"""
    project = ProjectFactory.create(**kwargs)
    projects_repositories.apply_template_to_project_sync(
        project=project, template=template
    )

    admin_role = project.roles.get(is_admin=True)
    ProjectMembershipFactory.create(
        user=project.created_by, project=project, role=admin_role
    )

    return project


def build_project(**kwargs):
    return ProjectFactory.build(**kwargs)
