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

import random

from asgiref.sync import sync_to_async
from django.contrib.auth.hashers import make_password
from django.db import transaction
from faker import Faker

from base.sampledata import factories
from commons.colors import NUM_COLORS
from permissions import choices
from projects.memberships import repositories as pj_memberships_repositories
from projects.memberships.models import ProjectMembership
from projects.projects import services as projects_services
from projects.projects.models import Project
from projects.roles.models import ProjectRole
from users.models import User
from workflows.models import Workflow, WorkflowStatus
from workspaces.memberships import repositories as ws_memberships_repositories
from workspaces.workspaces import services as workspaces_services
from workspaces.workspaces.models import Workspace

fake: Faker = Faker()
Faker.seed(0)
random.seed(0)

################################
# CONSTANTS
################################

# Users
NUM_USERS = 105
PASSWORD = make_password("123123")

################################


@transaction.atomic
async def load_test_data() -> None:
    # USERS. Create users
    print("  - Creating sample users")
    all_users = await _create_users()
    users = all_users[:10]

    # WORKSPACES
    # create one basic workspace per user
    print("  - Creating sample workspaces")
    workspaces = []
    for user in users:
        workspace = await factories.create_workspace(created_by=user)
        workspaces.append(workspace)

    # create memberships for workspaces
    for workspace in workspaces:
        await _create_workspace_memberships(workspace=workspace, users=users)

    # PROJECTS
    print("  - Creating sample projects")
    projects = []
    for workspace in workspaces:
        # create one project (kanban) in each workspace with the same creator
        # it applies a template and creates also admin and general roles
        if workspace.created_by:
            project = await factories.create_project(
                workspace=workspace, created_by=workspace.created_by
            )

        # add other users to different roles (admin and general)
        await factories.create_project_memberships(project_id=project.id, users=users)
        projects.append(await factories.get_project_with_related_info(project.id))

    for project in projects:
        # PROJECT INVITATIONS
        await factories.create_project_invitations(project=project, users=users)

        # STORIES
        await factories.create_stories(project_id=project.id, with_comments=True)

    # CUSTOM PROJECTS
    print("  - Creating scenarios to check permissions")
    custom_user = users[0]
    workspace = await factories.create_workspace(
        created_by=custom_user, name="Custom workspace"
    )
    await _create_empty_project(created_by=custom_user, workspace=workspace)
    await _create_inconsistent_permissions_project(
        created_by=custom_user, workspace=workspace
    )
    await _create_project_with_several_roles(
        created_by=custom_user, workspace=workspace, users=users
    )
    await _create_project_membership_scenario()

    # CUSTOM SCENARIOS
    print("  - Creating scenario to check project invitations")
    await _create_scenario_with_invitations()
    print("  - Creating scenario to check user searching")
    await _create_scenario_for_searches()
    print("  - Creating scenario to check revoke invitations")
    await _create_scenario_for_revoke()
    print("  - Creating scenarios to check big kanbans")
    await _create_scenario_with_1k_stories(
        workspace=workspace, created_by=custom_user, users=all_users
    )
    await _create_scenario_with_2k_stories_and_40_workflow_statuses(
        workspace=workspace, created_by=custom_user, users=all_users
    )


################################
# USERS
################################


async def _create_users() -> list[User]:
    users = [await _create_user(index=i + 1, save=False) for i in range(NUM_USERS)]
    await User.objects.abulk_create(users)
    return [
        u
        async for u in User.objects.all()
        .exclude(username="admin")
        .order_by("date_joined")
    ]


async def _create_user(index: int, save: bool = True) -> User:
    username = f"{index}user"
    email = f"{username}@tenzu.demo"
    full_name = fake.name()
    color = fake.random_int(min=1, max=NUM_COLORS)
    user = User(
        username=username,
        email=email,
        full_name=full_name,
        color=color,
        is_active=True,
        password=PASSWORD,
    )
    if save:
        await sync_to_async(user.save)()
    return user


################################
# WORKSPACES
################################


async def _create_workspace_memberships(
    workspace: Workspace, users: list[User]
) -> None:
    # get users except the creator of the workspace
    users = [u for u in users if u.id != workspace.created_by_id]

    # add 0 - 4 members
    num_members = random.randint(0, 4)
    for user in users[:num_members]:
        await ws_memberships_repositories.create_workspace_membership(
            user=user, workspace=workspace
        )


################################
# PROJECTS
################################


@sync_to_async
def _create_project_role(project: Project, name: str | None = None) -> ProjectRole:
    name = name or fake.word()
    return ProjectRole.objects.create(
        project=project,
        name=name,
        is_admin=False,
        permissions=choices.ProjectPermissions.values,
    )


@sync_to_async
def _get_project_other_roles(project: Project) -> list[ProjectRole]:
    return list(project.roles.exclude(slug="admin"))


@sync_to_async
def _list_project_members(project: Project) -> list[User]:
    return list(project.members.all())


@sync_to_async
def _get_membership_user(membership: ProjectMembership) -> User:
    return membership.user


@sync_to_async
def _get_membership_role(membership: ProjectMembership) -> ProjectRole:
    return membership.role


#################################
# WORKFLOWS
#################################


@sync_to_async
def _get_workflows(project: Project) -> list[Workflow]:
    return list(project.workflows.all())


@sync_to_async
def _get_workflow_statuses(workflow: Workflow) -> list[WorkflowStatus]:
    return list(workflow.statuses.all())


async def _create_workflow_status(
    workflow: Workflow,
    name: str | None = None,
    color: int | None = None,
) -> None:
    await WorkflowStatus.objects.acreate(
        name=name or fake.unique.text(max_nb_chars=15)[:-1],
        color=color or fake.random_int(min=1, max=NUM_COLORS),
        workflow=workflow,
    )


################################
# CUSTOM PROJECTS
################################


async def _create_empty_project(created_by: User, workspace: Workspace) -> None:
    await projects_services._create_project(
        name="Empty project",
        description=fake.paragraph(nb_sentences=2),
        color=fake.random_int(min=1, max=NUM_COLORS),
        created_by=created_by,
        workspace=workspace,
    )


async def _create_inconsistent_permissions_project(
    created_by: User, workspace: Workspace
) -> None:
    # give general role less permissions than public-permissions
    project = await factories.create_project(
        name="Inconsistent Permissions",
        created_by=created_by,
        workspace=workspace,
    )
    general_members_role = await sync_to_async(project.roles.get)(slug="general")
    general_members_role.permissions = ["view_story"]
    await sync_to_async(general_members_role.save)()
    project.public_permissions = choices.ProjectPermissions.values
    await sync_to_async(project.save)()


async def _create_project_with_several_roles(
    created_by: User, workspace: Workspace, users: list[User]
) -> None:
    project = await factories.create_project(
        name="Several Roles", created_by=created_by, workspace=workspace
    )
    await _create_project_role(project=project, name="UX/UI")
    await _create_project_role(project=project, name="Developer")
    await _create_project_role(project=project, name="Stakeholder")
    await factories.create_project_memberships(project_id=project.id, users=users)


async def _create_project_membership_scenario() -> None:
    user1000 = await _create_user(1000)
    user1001 = await _create_user(1001)
    user1002 = await _create_user(1002)
    user1003 = await _create_user(1003)  # noqa: F841

    # workspace: user1000 ws-member, user1001 ws-member
    workspace = await factories.create_workspace(
        created_by=user1000, name="u1001 is ws member"
    )
    await ws_memberships_repositories.create_workspace_membership(
        user=user1001, workspace=workspace
    )
    # project: user1000 pj-admin, user1001 pj-member
    project = await factories.create_project(
        workspace=workspace,
        created_by=user1000,
        name="pj 11",
        description="user1000 pj-admin, user1001 pj-member",
    )
    members_role = await sync_to_async(project.roles.get)(slug="general")
    await pj_memberships_repositories.create_project_membership(
        user=user1001, project=project, role=members_role
    )
    # project: user1000 pj-admin, user1001 pj-member without permissions
    project = await factories.create_project(
        workspace=workspace,
        created_by=user1000,
        name="pj 12",
        description="user1000 pj-admin, user1001 pj-member without permissions",
    )
    members_role = await sync_to_async(project.roles.get)(slug="general")
    await pj_memberships_repositories.create_project_membership(
        user=user1001, project=project, role=members_role
    )
    members_role.permissions = []
    await sync_to_async(members_role.save)()
    # project: user1000 pj-admin, user1001 not pj-member, ws-members not allowed
    await factories.create_project(
        workspace=workspace,
        created_by=user1000,
        name="pj 13",
        description="user1000 pj-admin, user1001 not pj-member, ws-members not allowed",
    )
    # project: user1000 pj-admin, user1001 not pj-member, ws-members allowed
    project = await factories.create_project(
        workspace=workspace,
        created_by=user1000,
        name="pj 14",
        description="user1000 pj-admin, user1001 not pj-member, ws-members allowed",
    )
    await sync_to_async(project.save)()
    # project: user1000 no pj-member, user1001 pj-admin, ws-members not allowed
    await factories.create_project(
        workspace=workspace,
        created_by=user1001,
        name="pj 15",
        description="user1000 no pj-member, user1001 pj-admin, ws-members not allowed",
    )
    # more projects
    # project: user1000 pj-admin, user1001 pj-member
    project = await factories.create_project(
        workspace=workspace,
        created_by=user1000,
        name="more - pj 16",
        description="user1000 pj-admin, user1001 pj-member",
    )
    members_role = await sync_to_async(project.roles.get)(slug="general")
    await pj_memberships_repositories.create_project_membership(
        user=user1001, project=project, role=members_role
    )
    # project: user1000 pj-admin, user1001 pj-member
    project = await factories.create_project(
        workspace=workspace,
        created_by=user1000,
        name="more - pj 17",
        description="user1000 pj-admin, user1001 pj-member",
    )
    members_role = await sync_to_async(project.roles.get)(slug="general")
    await pj_memberships_repositories.create_project_membership(
        user=user1001, project=project, role=members_role
    )
    # project: user1000 pj-admin, user1001 pj-member
    project = await factories.create_project(
        workspace=workspace,
        created_by=user1000,
        name="more - pj 18",
        description="user1000 pj-admin, user1001 pj-member",
    )
    members_role = await sync_to_async(project.roles.get)(slug="general")
    await pj_memberships_repositories.create_project_membership(
        user=user1001, project=project, role=members_role
    )
    # project: user1000 pj-admin, user1001 pj-member
    project = await factories.create_project(
        workspace=workspace,
        created_by=user1000,
        name="more - pj 19",
        description="user1000 pj-admin, user1001 pj-member",
    )
    members_role = await sync_to_async(project.roles.get)(slug="general")
    await pj_memberships_repositories.create_project_membership(
        user=user1001, project=project, role=members_role
    )
    # project: user1000 pj-admin, user1001 pj-member
    project = await factories.create_project(
        workspace=workspace,
        created_by=user1000,
        name="more - pj 20",
        description="user1000 pj-admin, user1001 pj-member",
    )
    members_role = await sync_to_async(project.roles.get)(slug="general")
    await pj_memberships_repositories.create_project_membership(
        user=user1001, project=project, role=members_role
    )

    # workspace: user1000 ws-member, user1001 ws-member, has_projects=true
    workspace = await factories.create_workspace(
        created_by=user1000, name="u1001 is ws member, hasProjects:T"
    )
    await ws_memberships_repositories.create_workspace_membership(
        user=user1001, workspace=workspace
    )
    # project: user1000 pj-admin, user1001 not pj-member, ws-members not allowed
    await factories.create_project(
        workspace=workspace,
        created_by=user1000,
        name="pj 21",
        description="user1000 pj-admin, user1001 not pj-member, ws-members not allowed",
    )
    # project: user1000 pj-admin, user1001 pj-member without permissions, ws-members allowed
    project = await factories.create_project(
        workspace=workspace,
        created_by=user1000,
        name="pj 22",
        description="user1000 pj-admin, user1001 pj-member without permissions, ws-members allowed",
    )
    members_role = await sync_to_async(project.roles.get)(slug="general")
    await pj_memberships_repositories.create_project_membership(
        user=user1001, project=project, role=members_role
    )
    members_role.permissions = []
    await sync_to_async(members_role.save)()
    await sync_to_async(project.save)()

    # workspace: user1000 ws-member, user1001 ws-member, has_projects=false
    workspace = await factories.create_workspace(
        created_by=user1000, name="u1001 is ws member, hasProjects:F"
    )
    await ws_memberships_repositories.create_workspace_membership(
        user=user1001, workspace=workspace
    )

    # workspace: user1000 ws-member, user1001 ws-guest
    workspace = await factories.create_workspace(
        created_by=user1000, name="u1001 ws guest"
    )
    # project: user1000 pj-admin, user1001 pj-member
    project = await factories.create_project(
        workspace=workspace,
        created_by=user1000,
        name="pj 41",
        description="user1000 pj-admin, user1001 pj-member",
    )
    members_role = await sync_to_async(project.roles.get)(slug="general")
    await pj_memberships_repositories.create_project_membership(
        user=user1001, project=project, role=members_role
    )
    # project: user1000 pj-member, user1001 pj-admin
    project = await factories.create_project(
        workspace=workspace,
        created_by=user1001,
        name="pj 42",
        description="user1000 pj-member, user1001 pj-admin",
    )
    members_role = await sync_to_async(project.roles.get)(slug="general")
    await pj_memberships_repositories.create_project_membership(
        user=user1000, project=project, role=members_role
    )
    # project: user1000 pj-admin, user1001 not pj-member, ws-allowed
    project = await factories.create_project(
        workspace=workspace,
        created_by=user1000,
        name="pj 43",
        description="user1000 pj-admin, user1001 not pj-member, ws-allowed",
    )
    await sync_to_async(project.save)()
    # project: user1000 pj-admin, user1001 pj-member without permissions, ws-members allowed
    project = await factories.create_project(
        workspace=workspace,
        created_by=user1000,
        name="pj 44",
        description="user1000 pj-admin, user1001 pj-member without permissions, ws-members allowed",
    )
    members_role = await sync_to_async(project.roles.get)(slug="general")
    await pj_memberships_repositories.create_project_membership(
        user=user1001, project=project, role=members_role
    )
    members_role.permissions = []
    await sync_to_async(project.save)()

    # workspace basic: user1000 & user1001 (ws-member), user1002/user1003 (ws-guest)
    workspace = await factories.create_workspace(
        created_by=user1000, name="uk/uk1 (ws-member), uk2/uk3 (ws-guest)"
    )
    await ws_memberships_repositories.create_workspace_membership(
        user=user1001, workspace=workspace
    )
    # project: u1000 pj-admin, u1002 pj-member without permissions, u1001/u1003 no pj-member, ws-members/public
    # not-allowed
    project = await factories.create_project(
        workspace=workspace,
        created_by=user1000,
        name="p45 pj-mb-NA ws-mb/public-NA",
        description="u1000 pj-admin, u1002 pj-member without permissions, u1001/u1003 no pj-member, ws-members/public "
        "not-allowed",
    )
    members_role = await sync_to_async(project.roles.get)(slug="general")
    members_role.permissions = []
    await sync_to_async(members_role.save)()
    await pj_memberships_repositories.create_project_membership(
        user=user1002, project=project, role=members_role
    )
    await sync_to_async(project.save)()
    # project: u1000 pj-admin, u1002 pj-member view_story, u1001/u1003 no pj-members ws-members/public not-allowed
    project = await factories.create_project(
        workspace=workspace,
        created_by=user1000,
        name="p46 pj-mb-view_story ws-mb/public-NA",
        description="project: u1000 pj-admin, u1002 pj-member view_story, u1001/u1003 no pj-members "
        "ws-members/public not-allowed",
    )
    members_role = await sync_to_async(project.roles.get)(slug="general")
    members_role.permissions = ["view_story"]
    await sync_to_async(members_role.save)()
    await pj_memberships_repositories.create_project_membership(
        user=user1002, project=project, role=members_role
    )
    await sync_to_async(project.save)()
    # project: u1k pj-admin, u1k2 pj-member view_story, u1k1/u1k3 no pj-member, public view-us, ws-members not-allowed
    project = await factories.create_project(
        workspace=workspace,
        created_by=user1000,
        name="p47 pj-mb-view_story ws-mb-NA public-viewUs",
        description="u1000 pj-admin, u1002 pj-member view_story, u1001/u1003 no pj-member, public view-us, ws-members "
        "not-allowed",
    )
    members_role = await sync_to_async(project.roles.get)(slug="general")
    members_role.permissions = ["view_story"]
    project.public_permissions = ["view_story"]
    await sync_to_async(members_role.save)()
    await pj_memberships_repositories.create_project_membership(
        user=user1002, project=project, role=members_role
    )
    await sync_to_async(project.save)()

    # workspace: user1000 (ws-member), user1001 (ws-member), user1002 (ws-guest), user1003 (ws-guest)
    workspace = await factories.create_workspace(
        created_by=user1000, name="uk-ws-adm uk1-ws-mb uk2/uk3-ws-guest"
    )
    await ws_memberships_repositories.create_workspace_membership(
        user=user1001, workspace=workspace
    )
    # project: u1k pj-admin, u1k2 pj-member view_story, u1k1/u1k3 no pj-member, public view-us, ws-members not-allowed
    project = await factories.create_project(
        workspace=workspace,
        created_by=user1000,
        name="p48 pj-mb-view_story public-viewUs ws-mb-NA",
        description="u1000 pj-admin, u1002 pj-member view_story, u1001/u1003 no pj-member, public view-us, ws-members "
        "not-allowed",
    )
    members_role = await sync_to_async(project.roles.get)(slug="general")
    members_role.permissions = ["view_story"]
    project.public_permissions = ["view_story"]
    await sync_to_async(members_role.save)()
    await pj_memberships_repositories.create_project_membership(
        user=user1002, project=project, role=members_role
    )
    await sync_to_async(project.save)()

    # workspace: user1000 (ws-member), user1001/user1002 (ws-member), user1003 (ws-guest)
    workspace = await factories.create_workspace(
        created_by=user1000, name="uk-ws-member uk1/k2-ws-mb uk3-ws-guest"
    )
    await ws_memberships_repositories.create_workspace_membership(
        user=user1001, workspace=workspace
    )
    await ws_memberships_repositories.create_workspace_membership(
        user=user1002, workspace=workspace
    )
    # project: u1k pj-admin, u1k2 pj-member view_story, u1k1/u1k3 no pj-member, public view-us, ws-members not-allowed
    project = await factories.create_project(
        workspace=workspace,
        created_by=user1000,
        name="p49 pj-mb-view_story public-viewUs ws-mb-NA",
        description="u1000 pj-admin, u1002 pj-member view_story, u1001/u1003 no pj-member, public view-us, ws-members "
        "not-allowed",
    )
    members_role = await sync_to_async(project.roles.get)(slug="general")
    members_role.permissions = ["view_story"]
    project.public_permissions = ["view_story"]
    await sync_to_async(members_role.save)()
    await pj_memberships_repositories.create_project_membership(
        user=user1002, project=project, role=members_role
    )
    await sync_to_async(project.save)()


################################
# CUSTOM SCENARIOS
################################


async def _create_scenario_with_invitations() -> None:
    user900 = await _create_user(900)
    user901 = await _create_user(901)

    # user900 is member of several workspaces
    ws1 = await workspaces_services._create_workspace(
        name="ws1 for members", created_by=user900, color=2
    )
    ws2 = await workspaces_services._create_workspace(
        name="ws2 for members allowed(p)", created_by=user900, color=2
    )
    await sync_to_async(ws2.save)()
    ws3 = await workspaces_services._create_workspace(
        name="ws3 for members not allowed(p)", created_by=user900, color=2
    )
    await sync_to_async(ws3.save)()
    await workspaces_services._create_workspace(
        name="ws4 for guests", created_by=user900, color=2
    )
    ws5 = await workspaces_services._create_workspace(
        name="ws5 lots of projects", created_by=user900, color=2
    )

    # user901 is member of ws1
    await ws_memberships_repositories.create_workspace_membership(
        user=user901, workspace=ws1
    )

    # user901 is member of ws2
    await ws_memberships_repositories.create_workspace_membership(
        user=user901, workspace=ws2
    )

    # user901 is member of ws3
    await ws_memberships_repositories.create_workspace_membership(
        user=user901, workspace=ws3
    )

    # user900 creates a project in ws1
    await factories.create_project(workspace=ws1, created_by=user900)

    # user900 creates a project in ws2 with ws-members allowed
    pj2 = await factories.create_project(workspace=ws2, created_by=user900)
    await sync_to_async(pj2.save)()

    # user900 creates a project in ws3 with ws-members not allowed
    await factories.create_project(workspace=ws3, created_by=user900)

    # user900 creates 7 projects in ws5 and user901 is member of these
    pj = await factories.create_project(workspace=ws5, created_by=user900)
    pj_member_role = (await _get_project_other_roles(project=pj))[0]
    await pj_memberships_repositories.create_project_membership(
        user=user901, project=pj, role=pj_member_role
    )
    pj = await factories.create_project(workspace=ws5, created_by=user900)
    pj_member_role = (await _get_project_other_roles(project=pj))[0]
    await pj_memberships_repositories.create_project_membership(
        user=user901, project=pj, role=pj_member_role
    )
    pj = await factories.create_project(workspace=ws5, created_by=user900)
    pj_member_role = (await _get_project_other_roles(project=pj))[0]
    await pj_memberships_repositories.create_project_membership(
        user=user901, project=pj, role=pj_member_role
    )
    pj = await factories.create_project(workspace=ws5, created_by=user900)
    pj_member_role = (await _get_project_other_roles(project=pj))[0]
    await pj_memberships_repositories.create_project_membership(
        user=user901, project=pj, role=pj_member_role
    )
    pj = await factories.create_project(workspace=ws5, created_by=user900)
    pj_member_role = (await _get_project_other_roles(project=pj))[0]
    await pj_memberships_repositories.create_project_membership(
        user=user901, project=pj, role=pj_member_role
    )
    pj = await factories.create_project(workspace=ws5, created_by=user900)
    pj_member_role = (await _get_project_other_roles(project=pj))[0]
    await pj_memberships_repositories.create_project_membership(
        user=user901, project=pj, role=pj_member_role
    )
    pj = await factories.create_project(workspace=ws5, created_by=user900)
    pj_member_role = (await _get_project_other_roles(project=pj))[0]
    await pj_memberships_repositories.create_project_membership(
        user=user901, project=pj, role=pj_member_role
    )


async def _create_scenario_for_searches() -> None:
    # some users
    user800 = await _create_user(800)
    elettescar = await factories.create_user(
        username="elettescar", full_name="Martina Eaton"
    )
    electra = await factories.create_user(username="electra", full_name="Sonia Moreno")
    await factories.create_user(username="danvers", full_name="Elena Riego")
    await factories.create_user(username="storm", full_name="Martina Elliott")
    await factories.create_user(username="elmarv", full_name="Joanna Marinari")

    # user800 is member of ws1
    ws1 = await workspaces_services._create_workspace(
        name="ws for searches(p)", created_by=user800, color=2
    )
    await sync_to_async(ws1.save)()

    # elettescar is member of ws1
    await ws_memberships_repositories.create_workspace_membership(
        user=elettescar, workspace=ws1
    )

    # electra is pj member of a project in ws1
    pj1 = await factories.create_project(workspace=ws1, created_by=user800)
    pj_member_role = (await _get_project_other_roles(project=pj1))[0]
    await pj_memberships_repositories.create_project_membership(
        user=electra, project=pj1, role=pj_member_role
    )


async def _create_scenario_for_revoke() -> None:
    # some users
    user1 = await factories.create_user(
        username="pruebastenzu1",
        full_name="Pruebas Tenzu 1",
        email="pruebastenzu+1@gmail.com",
    )
    user2 = await factories.create_user(
        username="pruebastenzu2",
        full_name="Pruebas Tenzu 2",
        email="pruebastenzu+2@gmail.com",
    )
    user3 = await factories.create_user(
        username="pruebastenzu3",
        full_name="Pruebas Tenzu 3",
        email="pruebastenzu+3@gmail.com",
    )
    user4 = await factories.create_user(
        username="pruebastenzu4",
        full_name="Pruebas Tenzu 4",
        email="pruebastenzu+4@gmail.com",
    )

    ws = await workspaces_services._create_workspace(
        name="ws for revoking(p)", created_by=user1, color=2
    )
    await sync_to_async(ws.save)()

    await ws_memberships_repositories.create_workspace_membership(
        user=user4, workspace=ws
    )
    await ws_memberships_repositories.create_workspace_membership(
        user=user2, workspace=ws
    )

    pj = await factories.create_project(workspace=ws, created_by=user1)
    pj_member_role = (await _get_project_other_roles(project=pj))[0]
    await pj_memberships_repositories.create_project_membership(
        user=user3, project=pj, role=pj_member_role
    )


async def _create_scenario_with_1k_stories(
    workspace: Workspace, users: list[User], created_by: User
) -> None:
    """
    Create a new project with 1000 stories.
    """
    project = await factories.create_project(
        name="1k Stories",
        description="This project contains 1000 stories.",
        created_by=created_by,
        workspace=workspace,
    )
    await factories.create_project_memberships(project_id=project.id, users=users)

    await factories.create_stories(
        project_id=project.id, min_stories=1000, with_comments=True
    )


async def _create_scenario_with_2k_stories_and_40_workflow_statuses(
    workspace: Workspace, users: list[User], created_by: User
) -> None:
    """
    Create a new project with 2000 stories and 40 statuses.
    """
    project = await factories.create_project(
        name="2k Stories, 40 statuses",
        description="This project contains 2000 stories and 40 statuses.",
        created_by=created_by,
        workspace=workspace,
    )
    await factories.create_project_memberships(project_id=project.id, users=users)

    workflow = (await _get_workflows(project=project))[0]
    for i in range(0, 40 - len(await _get_workflow_statuses(workflow=workflow))):
        await _create_workflow_status(workflow=workflow)

    await factories.create_stories(
        project_id=project.id, min_stories=2000, with_comments=True
    )
