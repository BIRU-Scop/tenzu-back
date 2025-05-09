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
from operator import attrgetter

from asgiref.sync import async_to_sync, sync_to_async

from memberships.choices import InvitationStatus
from permissions import choices
from projects.projects import repositories as projects_repositories

from ..utils import set_prefetched_qs_cache
from .base import Factory, factory

# PROJECT ROLE


class ProjectRoleFactory(Factory):
    name = factory.Sequence(lambda n: f"Role {n}")
    slug = factory.Sequence(lambda n: f"test-role-{n}")
    permissions = choices.ProjectPermissions.values
    project = factory.SubFactory("tests.utils.factories.ProjectFactory")

    class Meta:
        model = "projects_memberships.ProjectRole"


@sync_to_async
def create_project_role(**kwargs):
    return ProjectRoleFactory.create(**kwargs)


def build_project_role(**kwargs):
    return ProjectRoleFactory.build(**kwargs)


# PROJECT MEMBERSHIP


class ProjectMembershipFactory(Factory):
    user = factory.SubFactory("tests.utils.factories.UserFactory")
    project = factory.SubFactory("tests.utils.factories.ProjectFactory")
    role = factory.SubFactory(
        "tests.utils.factories.ProjectRoleFactory",
        project=factory.SelfAttribute("..project"),
    )

    class Meta:
        model = "projects_memberships.ProjectMembership"


@sync_to_async
def create_project_membership(**kwargs):
    return ProjectMembershipFactory.create(**kwargs)


def build_project_membership(**kwargs):
    return ProjectMembershipFactory.build(**kwargs)


# PROJECT INVITATION


class ProjectInvitationFactory(Factory):
    status = InvitationStatus.PENDING
    email = factory.Sequence(lambda n: f"user{n}@email.com")
    user = factory.SubFactory("tests.utils.factories.UserFactory")
    project = factory.SubFactory("tests.utils.factories.ProjectFactory")
    role = factory.SubFactory(
        "tests.utils.factories.ProjectRoleFactory",
        project=factory.SelfAttribute("..project"),
    )
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
    workspace = factory.SubFactory(
        "tests.utils.factories.WorkspaceFactory",
        created_by=factory.SelfAttribute("..created_by"),
    )

    class Meta:
        model = "projects.Project"


@sync_to_async
def create_simple_project(**kwargs):
    return ProjectFactory.create(**kwargs)


@sync_to_async
def create_project(template, **kwargs):
    """Create project and its dependencies"""
    if "workspace" in kwargs and "created_by" not in kwargs:
        kwargs["created_by"] = kwargs["workspace"].created_by
    project = ProjectFactory.create(**kwargs)
    roles = async_to_sync(projects_repositories.apply_template_to_project)(
        project=project, template=template
    )

    owner_role = next(filter(attrgetter("is_owner"), roles))
    owner_membership = ProjectMembershipFactory.create(
        user=project.created_by, project=project, role=owner_role
    )
    set_prefetched_qs_cache(
        project, {"roles": roles, "memberships": [owner_membership]}
    )

    return project


def build_project(**kwargs):
    return ProjectFactory.build(**kwargs)


# PROJECT


class ProjectTemplateFactory(Factory):
    name = factory.Sequence(lambda n: f"Project Template {n}")
    slug = factory.Sequence(lambda n: f"template-{n}")
    roles = []
    workflows = [{"slug": "main", "name": "Main", "order": 1}]
    workflow_statuses = []

    class Meta:
        model = "projects.ProjectTemplate"


def build_project_template(**kwargs):
    return ProjectTemplateFactory.build(**kwargs)
