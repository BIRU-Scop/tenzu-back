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
from faker import Faker

from base.sampledata import factories
from commons.colors import NUM_COLORS
from commons.utils import transaction_atomic_async
from permissions.choices import ProjectPermissions
from projects.memberships import repositories as pj_memberships_repositories
from projects.memberships.models import ProjectMembership, ProjectRole
from projects.projects import services as projects_services
from projects.projects.models import Project
from users.models import User
from workflows.models import Workflow, WorkflowStatus
from workspaces.memberships import repositories as ws_memberships_repositories
from workspaces.memberships.models import WorkspaceRole
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


@transaction_atomic_async
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
        await factories.create_workspace_memberships(workspace=workspace, users=users)

    # PROJECTS
    print("  - Creating sample projects")
    projects = []
    for workspace in workspaces:
        # create one project (kanban) in each workspace with the same creator
        # it applies a template and creates also owner and other roles
        project = await factories.create_project(
            workspace=workspace, created_by=workspace.created_by
        )

        # add other users to different roles
        full_project = await factories.get_project_with_related_info(project.id)
        await factories.create_project_memberships(project=full_project, users=users)
        projects.append(full_project)

    for project in projects:
        # PROJECT INVITATIONS
        await factories.create_project_invitations(project=project, users=users)

        # STORIES
        await factories.create_stories(project=project, with_comments=True)

    # CUSTOM PROJECTS
    print("  - Creating scenarios to check permissions")
    custom_user = users[0]
    workspace = await factories.create_workspace(
        created_by=custom_user, name="Custom workspace"
    )
    await factories.create_workspace_memberships(workspace=workspace, users=all_users)
    await _create_empty_project(created_by=custom_user, workspace=workspace)
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
# PROJECTS
################################


@sync_to_async
def _create_project_role(project: Project, name: str | None = None) -> ProjectRole:
    name = name or fake.word()
    return ProjectRole.objects.create(
        project=project,
        name=name,
        is_owner=False,
        permissions=[
            ProjectPermissions.VIEW_STORY.value,
            ProjectPermissions.MODIFY_STORY.value,
            ProjectPermissions.CREATE_STORY.value,
            ProjectPermissions.DELETE_STORY.value,
            ProjectPermissions.VIEW_COMMENT.value,
            ProjectPermissions.CREATE_MODIFY_DELETE_COMMENT.value,
            ProjectPermissions.VIEW_WORKFLOW.value,
            ProjectPermissions.MODIFY_WORKFLOW.value,
            ProjectPermissions.CREATE_WORKFLOW.value,
            ProjectPermissions.DELETE_WORKFLOW.value,
        ],
    )


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


async def _create_project_with_several_roles(
    created_by: User, workspace: Workspace, users: list[User]
) -> None:
    project = await factories.create_project(
        name="Several Roles", created_by=created_by, workspace=workspace
    )
    await _create_project_role(project=project, name="UX/UI")
    await _create_project_role(project=project, name="Developer")
    await _create_project_role(project=project, name="Stakeholder")
    await factories.create_project_memberships(
        await factories.get_project_with_related_info(project.id), users=users
    )


async def _create_project_membership_scenario() -> None:
    user1000 = await _create_user(1000)
    user1001 = await _create_user(1001)
    user1002 = await _create_user(1002)
    user1003 = await _create_user(1003)  # noqa: F841

    # workspace: user1000 ws-member, user1001 ws-member
    workspace = await factories.create_workspace(
        created_by=user1000, name="u1001 is ws member"
    )
    workspace_role = await ws_memberships_repositories.get_role(
        WorkspaceRole,
        filters={"workspace_id": workspace.id, "slug": "member"},
    )
    await ws_memberships_repositories.create_workspace_membership(
        user=user1001, workspace=workspace, role=workspace_role
    )
    # project: user1000 pj-owner, user1001 pj-member
    project = await factories.create_project(
        workspace=workspace,
        created_by=user1000,
        name="pj 11",
        description="user1000 pj-owner, user1001 pj-member",
    )
    project_role = await ws_memberships_repositories.get_role(
        ProjectRole,
        filters={"project_id": project.id, "slug": "member"},
    )
    await pj_memberships_repositories.create_project_membership(
        user=user1001, project=project, role=project_role
    )
    # project: user1000 pj-owner, user1001 pj-member without permissions
    project = await factories.create_project(
        workspace=workspace,
        created_by=user1000,
        name="pj 12",
        description="user1000 pj-owner, user1001 pj-member without permissions",
    )
    project_role = await ws_memberships_repositories.get_role(
        ProjectRole,
        filters={"project_id": project.id, "slug": "member", "editable": True},
    )
    await pj_memberships_repositories.create_project_membership(
        user=user1001, project=project, role=project_role
    )
    project_role.permissions = []
    await project_role.asave()
    # project: user1000 pj-owner, user1001 not pj-member
    await factories.create_project(
        workspace=workspace,
        created_by=user1000,
        name="pj 13",
        description="user1000 pj-owner, user1001 not pj-member",
    )
    # project: user1000 pj-owner, user1001 not pj-member
    await factories.create_project(
        workspace=workspace,
        created_by=user1000,
        name="pj 14",
        description="user1000 pj-owner, user1001 not pj-member",
    )
    # project: user1000 no pj-member, user1001 pj-owner, pj-members without permissions
    project = await factories.create_project(
        workspace=workspace,
        created_by=user1001,
        name="pj 15",
        description="user1000 no pj-member, user1001 pj-owner, pj-members without permissions",
    )
    project_role = await ws_memberships_repositories.get_role(
        ProjectRole,
        filters={"project_id": project.id, "slug": "member", "editable": True},
    )
    project_role.permissions = []
    await project_role.asave()
    # more projects
    # project: user1000 pj-owner, user1001 pj-member
    project = await factories.create_project(
        workspace=workspace,
        created_by=user1000,
        name="more - pj 16",
        description="user1000 pj-owner, user1001 pj-member",
    )
    project_role = await ws_memberships_repositories.get_role(
        ProjectRole,
        filters={"project_id": project.id, "slug": "member"},
    )
    await pj_memberships_repositories.create_project_membership(
        user=user1001, project=project, role=project_role
    )
    # project: user1000 pj-owner, user1001 pj-member
    project = await factories.create_project(
        workspace=workspace,
        created_by=user1000,
        name="more - pj 17",
        description="user1000 pj-owner, user1001 pj-member",
    )
    project_role = await ws_memberships_repositories.get_role(
        ProjectRole,
        filters={"project_id": project.id, "slug": "member"},
    )
    await pj_memberships_repositories.create_project_membership(
        user=user1001, project=project, role=project_role
    )
    # project: user1000 pj-owner, user1001 pj-member
    project = await factories.create_project(
        workspace=workspace,
        created_by=user1000,
        name="more - pj 18",
        description="user1000 pj-owner, user1001 pj-member",
    )
    project_role = await ws_memberships_repositories.get_role(
        ProjectRole,
        filters={"project_id": project.id, "slug": "member"},
    )
    await pj_memberships_repositories.create_project_membership(
        user=user1001, project=project, role=project_role
    )
    # project: user1000 pj-owner, user1001 pj-member
    project = await factories.create_project(
        workspace=workspace,
        created_by=user1000,
        name="more - pj 19",
        description="user1000 pj-owner, user1001 pj-member",
    )
    project_role = await ws_memberships_repositories.get_role(
        ProjectRole,
        filters={"project_id": project.id, "slug": "member"},
    )
    await pj_memberships_repositories.create_project_membership(
        user=user1001, project=project, role=project_role
    )
    # project: user1000 pj-owner, user1001 pj-member
    project = await factories.create_project(
        workspace=workspace,
        created_by=user1000,
        name="more - pj 20",
        description="user1000 pj-owner, user1001 pj-member",
    )
    project_role = await ws_memberships_repositories.get_role(
        ProjectRole,
        filters={"project_id": project.id, "slug": "member"},
    )
    await pj_memberships_repositories.create_project_membership(
        user=user1001, project=project, role=project_role
    )

    # workspace: user1000 ws-member, user1001 ws-member, has_projects=true
    workspace = await factories.create_workspace(
        created_by=user1000, name="u1001 is ws member, hasProjects:T"
    )
    workspace_role = await ws_memberships_repositories.get_role(
        WorkspaceRole,
        filters={"workspace_id": workspace.id, "slug": "member"},
    )
    await ws_memberships_repositories.create_workspace_membership(
        user=user1001, workspace=workspace, role=workspace_role
    )
    # project: user1000 pj-owner, user1001 not pj-member
    await factories.create_project(
        workspace=workspace,
        created_by=user1000,
        name="pj 21",
        description="user1000 pj-owner, user1001 not pj-member",
    )
    # project: user1000 pj-owner, user1001 pj-member without permissions
    project = await factories.create_project(
        workspace=workspace,
        created_by=user1000,
        name="pj 22",
        description="user1000 pj-owner, user1001 pj-member without permissions",
    )
    project_role = await ws_memberships_repositories.get_role(
        ProjectRole,
        filters={"project_id": project.id, "slug": "member"},
    )
    await pj_memberships_repositories.create_project_membership(
        user=user1001, project=project, role=project_role
    )
    project_role.permissions = []
    await project_role.asave()

    # workspace: user1000 ws-member, user1001 ws-member, has_projects=false
    workspace = await factories.create_workspace(
        created_by=user1000, name="u1001 is ws member, hasProjects:F"
    )
    workspace_role = await ws_memberships_repositories.get_role(
        WorkspaceRole,
        filters={"workspace_id": workspace.id, "slug": "member"},
    )
    await ws_memberships_repositories.create_workspace_membership(
        user=user1001, workspace=workspace, role=workspace_role
    )

    # workspace: user1000 ws-member, user1001 ws-guest
    workspace = await factories.create_workspace(
        created_by=user1000, name="u1001 pj readonly-member"
    )
    # project: user1000 pj-owner, user1001 pj-readonly-invitee
    project = await factories.create_project(
        workspace=workspace,
        created_by=user1000,
        name="pj 41",
        description="user1000 pj-owner, user1001 pj-readonly-invitee",
    )
    project_role = await ws_memberships_repositories.get_role(
        ProjectRole,
        filters={"project_id": project.id, "slug": "readonly-member"},
    )
    await factories.create_project_invitation(
        user=user1001, project=project, role=project_role
    )
    # project: user1000 pj-owner, user1001 pj-owner-invitee
    project = await factories.create_project(
        workspace=workspace,
        created_by=user1000,
        name="pj 42",
        description="user1000 pj-owner, user1001 pj-owner-invitee",
    )
    project_role = await ws_memberships_repositories.get_role(
        ProjectRole,
        filters={"project_id": project.id, "slug": "owner"},
    )
    await factories.create_project_invitation(
        user=user1001, project=project, role=project_role
    )
    # project: user1000 pj-owner, user1001 not pj-member
    project = await factories.create_project(
        workspace=workspace,
        created_by=user1000,
        name="pj 43",
        description="user1000 pj-owner, user1001 not pj-member",
    )
    # project: user1000 pj-owner, user1001 pj-member without permissions, ws-members allowed
    project = await factories.create_project(
        workspace=workspace,
        created_by=user1000,
        name="pj 44",
        description="user1000 pj-owner, user1001 pj-member-invitee without permissions",
    )
    project_role = await ws_memberships_repositories.get_role(
        ProjectRole,
        filters={"project_id": project.id, "slug": "member"},
    )
    project_role.permissions = []
    await project_role.asave()
    await factories.create_project_invitation(
        user=user1001, project=project, role=project_role
    )

    # workspace basic: user1000-owner, user1001-admin, user1002-readonly-member, user1003-member
    workspace = await factories.create_workspace(
        created_by=user1000,
        name="user1000-owner, one user for each role",
    )
    workspace_role = await ws_memberships_repositories.get_role(
        WorkspaceRole,
        filters={"workspace_id": workspace.id, "slug": "admin"},
    )
    await ws_memberships_repositories.create_workspace_membership(
        user=user1001, workspace=workspace, role=workspace_role
    )
    workspace_role = await ws_memberships_repositories.get_role(
        WorkspaceRole,
        filters={"workspace_id": workspace.id, "slug": "readonly-member"},
    )
    await ws_memberships_repositories.create_workspace_membership(
        user=user1002, workspace=workspace, role=workspace_role
    )
    workspace_role = await ws_memberships_repositories.get_role(
        WorkspaceRole,
        filters={"workspace_id": workspace.id, "slug": "member"},
    )
    await ws_memberships_repositories.create_workspace_membership(
        user=user1003, workspace=workspace, role=workspace_role
    )
    # project: u1000 pj-owner, u1002 pj-member without permissions, u1001/u1003 no pj-member
    # not-allowed
    project = await factories.create_project(
        workspace=workspace,
        created_by=user1000,
        name="p45 pj-mb-NA ws-mb/public-NA",
        description="u1000 pj-owner, u1002 pj-member without permissions, u1001/u1003 no pj-member "
        "not-allowed",
    )
    project_role = await ws_memberships_repositories.get_role(
        ProjectRole,
        filters={"project_id": project.id, "slug": "member"},
    )
    project_role.permissions = []
    await project_role.asave()
    await pj_memberships_repositories.create_project_membership(
        user=user1002, project=project, role=project_role
    )
    # project: u1000 pj-owner, u1002 pj-member view_story, u1001/u1003 no pj-members
    project = await factories.create_project(
        workspace=workspace,
        created_by=user1000,
        name="p46 pj-mb-view_story",
        description="project: u1000 pj-owner, u1002 pj-member view_story, u1001/u1003 no pj-members",
    )
    project_role = await ws_memberships_repositories.get_role(
        ProjectRole,
        filters={"project_id": project.id, "slug": "member"},
    )
    project_role.permissions = [ProjectPermissions.VIEW_STORY]
    await project_role.asave()
    await pj_memberships_repositories.create_project_membership(
        user=user1002, project=project, role=project_role
    )

    # workspace: user1000 (ws-owner), user1001 (ws-member), user1002 (ws-invitee), user1003 (ws-invitee)
    workspace = await factories.create_workspace(
        created_by=user1000, name="uk-ws-adm uk1-ws-mb uk2/uk3-ws-invitee"
    )
    workspace_role = await ws_memberships_repositories.get_role(
        WorkspaceRole,
        filters={"workspace_id": workspace.id, "slug": "member"},
    )
    await ws_memberships_repositories.create_workspace_membership(
        user=user1001, workspace=workspace, role=workspace_role
    )
    await factories.create_workspace_invitation(
        user=user1002, workspace=workspace, role=workspace_role
    )
    await factories.create_workspace_invitation(
        user=user1003, workspace=workspace, role=workspace_role
    )
    # project: u1k pj-owner, u1k1 pj-member view_story, u1k2/u1k3 no pj-member
    project = await factories.create_project(
        workspace=workspace,
        created_by=user1000,
        name="p48 pj-mb-view_story public-viewUs ws-mb-NA",
        description="u1000 pj-owner, u1001 pj-member view_story, u1002/u1003 no pj-member"
        "not-allowed",
    )
    project_role = await ws_memberships_repositories.get_role(
        ProjectRole,
        filters={"project_id": project.id, "slug": "member"},
    )
    project_role.permissions = [ProjectPermissions.VIEW_STORY]
    await project_role.asave()
    await pj_memberships_repositories.create_project_membership(
        user=user1001, project=project, role=project_role
    )

    # workspace: user1000 (ws-member), user1001/user1002 (ws-member), user1003 (ws-invitee)
    workspace = await factories.create_workspace(
        created_by=user1000, name="uk-ws-member uk1/k2-ws-mb uk3-ws-invitee"
    )
    workspace_role = await ws_memberships_repositories.get_role(
        WorkspaceRole,
        filters={"workspace_id": workspace.id, "slug": "member"},
    )
    await ws_memberships_repositories.create_workspace_membership(
        user=user1001, workspace=workspace, role=workspace_role
    )
    await ws_memberships_repositories.create_workspace_membership(
        user=user1002, workspace=workspace, role=workspace_role
    )
    await factories.create_workspace_invitation(
        user=user1003, workspace=workspace, role=workspace_role
    )
    # project: u1k pj-owner, u1k2 pj-member view_story, u1k1/u1k3 no pj-member
    project = await factories.create_project(
        workspace=workspace,
        created_by=user1000,
        name="p49 pj-mb-view_story public-viewUs ws-mb-NA",
        description="u1000 pj-owner, u1002 pj-member view_story, u1001/u1003 no pj-member",
    )
    project_role = await ws_memberships_repositories.get_role(
        ProjectRole,
        filters={"project_id": project.id, "slug": "member"},
    )
    project_role.permissions = [ProjectPermissions.VIEW_STORY]
    await project_role.asave()
    await pj_memberships_repositories.create_project_membership(
        user=user1002, project=project, role=project_role
    )


################################
# CUSTOM SCENARIOS
################################


async def _create_scenario_with_invitations() -> None:
    user900 = await _create_user(900)
    user901 = await _create_user(901)
    user902 = await _create_user(902)

    # user900 is member of several workspaces
    ws1 = (
        await workspaces_services._create_workspace(
            name="ws1 for members", created_by=user900, color=2
        )
    )[0]
    ws2 = (
        await workspaces_services._create_workspace(
            name="ws2 for members allowed(p)", created_by=user900, color=2
        )
    )[0]
    ws3 = (
        await workspaces_services._create_workspace(
            name="ws3 for members not allowed(p)", created_by=user900, color=2
        )
    )[0]
    ws4 = (
        await workspaces_services._create_workspace(
            name="ws4 for guests", created_by=user900, color=2
        )
    )[0]
    ws5 = (
        await workspaces_services._create_workspace(
            name="ws5 lots of projects", created_by=user900, color=2
        )
    )[0]

    workspace_role = await ws_memberships_repositories.get_role(
        WorkspaceRole,
        filters={"workspace_id": ws1.id, "slug": "member"},
    )
    # user901 is member of ws1
    await ws_memberships_repositories.create_workspace_membership(
        user=user901, workspace=ws1, role=workspace_role
    )

    workspace_role = await ws_memberships_repositories.get_role(
        WorkspaceRole,
        filters={"workspace_id": ws2.id, "slug": "member"},
    )
    # user901 is member of ws2
    await ws_memberships_repositories.create_workspace_membership(
        user=user901, workspace=ws2, role=workspace_role
    )

    workspace_role = await ws_memberships_repositories.get_role(
        WorkspaceRole,
        filters={"workspace_id": ws3.id, "slug": "member"},
    )
    # user901 is member of ws3
    await ws_memberships_repositories.create_workspace_membership(
        user=user901, workspace=ws3, role=workspace_role
    )
    # user902 is invited to ws3
    await factories.create_workspace_invitation(
        user=user902, workspace=ws3, role=workspace_role
    )

    # user900 creates a project in ws1
    await factories.create_project(workspace=ws1, created_by=user900)

    # user900 creates a project in ws2 and user901 is invited
    pj2 = await factories.create_project(workspace=ws2, created_by=user900)
    project_role = await pj_memberships_repositories.get_role(
        ProjectRole,
        filters={"project_id": pj2.id, "slug": "member"},
    )
    await factories.create_project_invitation(
        user=user901, project=pj2, role=project_role
    )

    # user900 creates a project in ws3 with ws-members not allowed
    await factories.create_project(workspace=ws3, created_by=user900)

    # user900 creates 7 projects in ws5 and user901 is invited to these with ≠ roles
    pj = await factories.create_project(workspace=ws5, created_by=user900)
    project_role = await ws_memberships_repositories.get_role(
        ProjectRole,
        filters={"project_id": pj.id, "slug": "readonly-member"},
    )
    await factories.create_project_invitation(
        user=user901, project=pj, role=project_role
    )
    pj = await factories.create_project(workspace=ws5, created_by=user900)
    project_role = await ws_memberships_repositories.get_role(
        ProjectRole,
        filters={"project_id": pj.id, "slug": "readonly-member"},
    )
    await factories.create_project_invitation(
        user=user901, project=pj, role=project_role
    )
    pj = await factories.create_project(workspace=ws5, created_by=user900)
    project_role = await ws_memberships_repositories.get_role(
        ProjectRole,
        filters={"project_id": pj.id, "slug": "admin"},
    )
    await factories.create_project_invitation(
        user=user901, project=pj, role=project_role
    )
    pj = await factories.create_project(workspace=ws5, created_by=user900)
    project_role = await ws_memberships_repositories.get_role(
        ProjectRole,
        filters={"project_id": pj.id, "slug": "admin"},
    )
    await factories.create_project_invitation(
        user=user901, project=pj, role=project_role
    )
    pj = await factories.create_project(workspace=ws5, created_by=user900)
    project_role = await ws_memberships_repositories.get_role(
        ProjectRole,
        filters={"project_id": pj.id, "slug": "owner"},
    )
    await factories.create_project_invitation(
        user=user901, project=pj, role=project_role
    )
    pj = await factories.create_project(workspace=ws5, created_by=user900)
    project_role = await ws_memberships_repositories.get_role(
        ProjectRole,
        filters={"project_id": pj.id, "slug": "member"},
    )
    await factories.create_project_invitation(
        user=user901, project=pj, role=project_role
    )
    pj = await factories.create_project(workspace=ws5, created_by=user900)
    project_role = await ws_memberships_repositories.get_role(
        ProjectRole,
        filters={"project_id": pj.id, "slug": "member"},
    )
    await factories.create_project_invitation(
        user=user901, project=pj, role=project_role
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
    ws1 = (
        await workspaces_services._create_workspace(
            name="ws for searches(p)", created_by=user800, color=2
        )
    )[0]

    workspace_role = await ws_memberships_repositories.get_role(
        WorkspaceRole,
        filters={"workspace_id": ws1.id, "slug": "member"},
    )

    # elettescar is member of ws1
    await ws_memberships_repositories.create_workspace_membership(
        user=elettescar, workspace=ws1, role=workspace_role
    )
    # electra is member of ws1
    await ws_memberships_repositories.create_workspace_membership(
        user=electra, workspace=ws1, role=workspace_role
    )

    # electra is pj member of a project in ws1
    pj1 = await factories.create_project(workspace=ws1, created_by=user800)
    project_role = await ws_memberships_repositories.get_role(
        ProjectRole,
        filters={"project_id": pj1.id, "slug": "member"},
    )
    await pj_memberships_repositories.create_project_membership(
        user=electra, project=pj1, role=project_role
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

    ws = (
        await workspaces_services._create_workspace(
            name="ws for revoking(p)", created_by=user1, color=2
        )
    )[0]
    workspace_role = await ws_memberships_repositories.get_role(
        WorkspaceRole,
        filters={"workspace_id": ws.id, "slug": "member"},
    )

    await ws_memberships_repositories.create_workspace_membership(
        user=user4, workspace=ws, role=workspace_role
    )
    await ws_memberships_repositories.create_workspace_membership(
        user=user2, workspace=ws, role=workspace_role
    )
    await ws_memberships_repositories.create_workspace_membership(
        user=user3, workspace=ws, role=workspace_role
    )

    pj = await factories.create_project(workspace=ws, created_by=user1)
    project_role = await ws_memberships_repositories.get_role(
        ProjectRole,
        filters={"project_id": pj.id, "slug": "member"},
    )
    await pj_memberships_repositories.create_project_membership(
        user=user3, project=pj, role=project_role
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
    full_project = await factories.get_project_with_related_info(project.id)
    await factories.create_project_memberships(full_project, users=users)

    await factories.create_stories(
        project=full_project, min_stories=1000, with_comments=True
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
    full_project = await factories.get_project_with_related_info(project.id)
    await factories.create_project_memberships(full_project, users=users)

    workflow = (await _get_workflows(project=project))[0]
    for i in range(0, 40 - len(await _get_workflow_statuses(workflow=workflow))):
        await _create_workflow_status(workflow=workflow)

    await factories.create_stories(
        project=full_project, min_stories=2000, with_comments=True
    )
