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

from django.db import transaction

from base.sampledata import factories
from projects.invitations import repositories as pj_invitations_repositories
from projects.invitations.choices import ProjectInvitationStatus
from projects.invitations.models import ProjectInvitation
from projects.projects.models import Project
from users import repositories as users_repositories
from users.models import User
from workspaces.memberships import repositories as ws_memberships_repositories
from workspaces.workspaces.models import Workspace


@transaction.atomic
async def load_demo_data() -> None:
    # CUSTOM SCENARIOS
    print("  - Creating scenario to freelance user working for herself")
    await _create_scenario_freelance_working_for_herself()
    print("  - Creating scenario to freelance user working for others")
    await _create_scenario_freelance_working_for_others()
    print("  - Creating scenario to user in society working for others")
    await _create_scenario_user_in_society_working_for_others()
    print("  - Creating scenario to manager in society working for others")
    await _create_scenario_manager_in_society_working_for_others()
    print("  - Creating scenario to manager in society with big client")
    await _create_scenario_manager_in_society_with_big_client()
    print("  - Creating scenario to manager in society with own product")
    await _create_scenario_manager_in_society_with_own_product()
    print("  - Creating scenario to manager in big society with own product")
    await _create_scenario_manager_in_big_society_with_own_product()


async def _create_scenario_freelance_working_for_herself() -> None:
    # USERS
    usera0 = await factories.create_user(username="usera0")
    usera1 = await factories.create_user(username="usera1")
    userd0 = await factories.create_user(username="userd0")

    created_by = usera0
    # WORKSPACES
    # member role is created by default
    # usera0 ws-member
    # ws "World domination" with no other members
    workspace = await factories.create_workspace(
        created_by=created_by, name="World domination"
    )

    # PROJECTS
    # it applies a template and creates also admin and general roles
    # usera0 pj-admin
    projects = []

    # pj "The ong" userd0 pj-member/role:general
    ong_proj = await factories.create_project(
        workspace=workspace, name="The ong", created_by=created_by
    )
    projects.append(await factories.get_project_with_related_info(ong_proj.id))
    general_role = await ong_proj.roles.aget(slug="general")
    await factories.create_project_membership(
        project=ong_proj, user=userd0, role=general_role
    )

    # pj "My next idea" usera1 pj-member/role:general
    next_idea_proj = await factories.create_project(
        workspace=workspace, name="My next idea", created_by=created_by
    )
    projects.append(await factories.get_project_with_related_info(next_idea_proj.id))
    general_role = await next_idea_proj.roles.aget(slug="general")
    await factories.create_project_membership(
        project=next_idea_proj, user=usera1, role=general_role
    )

    # pj with no other members
    projects_names = ["My current idea", "My old idea"]
    for pj_name in projects_names:
        proj = await factories.create_project(
            workspace=workspace, name=pj_name, created_by=created_by
        )
        projects.append(await factories.get_project_with_related_info(proj.id))

    for project in projects:
        # PROJECT INVITATIONS
        await _create_accepted_project_invitations(project=project)

        # STORIES
        await factories.create_stories(project_id=project.id, with_comments=True)


async def _create_scenario_freelance_working_for_others() -> None:
    # USERS
    userb0 = await factories.create_user(username="userb0")
    userb1 = await factories.create_user(username="userb1")
    userb2 = await factories.create_user(username="userb2")
    userb3 = await factories.create_user(username="userb3")
    usera1 = await users_repositories.get_user(filters={"username_or_email": "usera1"})
    if not usera1:
        raise Exception("User usera1 not found")
    userd0 = await users_repositories.get_user(filters={"username_or_email": "userd0"})
    if not userd0:
        raise Exception("User userd0 not found")
    userd1 = await factories.create_user(username="userd1")
    userf0 = await factories.create_user(username="userf0")

    created_by = userb0

    # WORKSPACES
    # member role is created by default
    # userb0 ws-member
    # ws "My projects" with no other members
    ws_my_projects = await factories.create_workspace(
        created_by=created_by, name="My projects"
    )
    # ws "Projects" with no other members
    ws_projects = await factories.create_workspace(
        created_by=created_by, name="Projects"
    )
    # ws random-name with no other members
    ws_random_name = await factories.create_workspace(created_by=created_by)

    # PROJECTS
    # it applies a template and creates also admin and general roles
    # userb0 pj-admin
    projects = []

    # for ws "My projects"
    # pj with no other members
    projects_names = ["Holidays", "Great project"]
    for pj_name in projects_names:
        proj = await factories.create_project(
            workspace=ws_my_projects, name=pj_name, created_by=created_by
        )
        projects.append(await factories.get_project_with_related_info(proj.id))

    # for ws "Projects"
    # pj random-name userb1, userb2, userb3 pj-member/role:general
    proj = await factories.create_project(workspace=ws_projects, created_by=created_by)
    projects.append(await factories.get_project_with_related_info(proj.id))
    general_role = await proj.roles.aget(slug="general")
    await factories.create_project_membership(
        project=proj, user=userb1, role=general_role
    )
    await factories.create_project_membership(
        project=proj, user=userb2, role=general_role
    )
    await factories.create_project_membership(
        project=proj, user=userb3, role=general_role
    )

    # 2 pj random-name with no other members
    for i in range(2):
        proj = await factories.create_project(
            workspace=ws_projects, created_by=created_by
        )
        projects.append(await factories.get_project_with_related_info(proj.id))

    # pj random-name userf0 pj-member/role:general
    proj = await factories.create_project(workspace=ws_projects, created_by=created_by)
    projects.append(await factories.get_project_with_related_info(proj.id))
    general_role = await proj.roles.aget(slug="general")
    await factories.create_project_membership(
        project=proj, user=userf0, role=general_role
    )

    # pj random-name userb1, usera1, userd1 pj-member/role:general. userd0 pj-member/role:admin
    proj = await factories.create_project(workspace=ws_projects, created_by=created_by)
    projects.append(await factories.get_project_with_related_info(proj.id))
    general_role = await proj.roles.aget(slug="general")
    await factories.create_project_membership(
        project=proj, user=userb1, role=general_role
    )
    await factories.create_project_membership(
        project=proj, user=usera1, role=general_role
    )
    await factories.create_project_membership(
        project=proj, user=userd1, role=general_role
    )
    admin_role = await proj.roles.aget(slug="admin")
    await factories.create_project_membership(
        project=proj, user=userd0, role=admin_role
    )

    # for ws random-name
    # pj random-name userd0 pj-member/role:general
    proj = await factories.create_project(
        workspace=ws_random_name, created_by=created_by
    )
    projects.append(await factories.get_project_with_related_info(proj.id))
    general_role = await proj.roles.aget(slug="general")
    await factories.create_project_membership(
        project=proj, user=userd0, role=general_role
    )

    for project in projects:
        # PROJECT INVITATIONS
        await _create_accepted_project_invitations(project=project)

        # STORIES
        await factories.create_stories(project_id=project.id, with_comments=True)


async def _create_scenario_user_in_society_working_for_others() -> None:
    # USERS
    userc0 = await factories.create_user(username="userc0")
    created_by = userc0

    # WORKSPACES
    # member role is created by default
    # userc0 ws-member
    # ws "Personal" with no other members
    workspace = await factories.create_workspace(created_by=created_by, name="Personal")

    # PROJECTS
    # it applies a template and creates also admin and general roles
    # userc0 pj-admin
    projects = []

    # pj with no other members
    projects_names = ["TODO", "Holidays", "Family"]
    for pj_name in projects_names:
        proj = await factories.create_project(
            workspace=workspace, name=pj_name, created_by=created_by
        )
        projects.append(await factories.get_project_with_related_info(proj.id))

    for project in projects:
        # STORIES
        await factories.create_stories(project_id=project.id, with_comments=True)


async def _create_scenario_manager_in_society_working_for_others() -> None:
    # USERS
    userd0 = await users_repositories.get_user(filters={"username_or_email": "userd0"})
    if not userd0:
        raise Exception("User userd0 not found")
    userc0 = await users_repositories.get_user(filters={"username_or_email": "userc0"})
    if not userc0:
        raise Exception("User userc0 not found")
    # usersdx total 150
    usersdx = [
        await factories.create_user(username=f"userd{i+1}") for i in range(1, 150)
    ]  # userd1 already exist
    created_by = userd0

    # WORKSPACES
    # member role is created by default
    # userd0 ws-member
    ws_internal = await factories.create_workspace(
        created_by=created_by, name="Internal"
    )
    ws_projects = await factories.create_workspace(
        created_by=created_by, name="Projects"
    )

    workspaces = [ws_internal, ws_projects]
    # ws with ws-members between 0-10 of usersdx
    for ws in workspaces:
        num_ws_members = random.randint(0, 10)
        if num_ws_members > 0:
            await _create_workspace_memberships(
                workspace=ws, users=usersdx[:num_ws_members]
            )

    # ws "Personal" with no other members
    ws_personal = await factories.create_workspace(created_by=userd0, name="Personal")

    # PROJECTS
    # it applies a template and creates also admin and general roles
    # userd0 pj-admin
    projects = []

    # for ws "Internal"
    # pj with members between 0-150 of usersdx
    projects_names = ["Comms", "Human resources"]
    for pj_name in projects_names:
        proj = await factories.create_project(
            workspace=ws_internal, name=pj_name, created_by=created_by
        )
        projects.append(await factories.get_project_with_related_info(proj.id))

    # pj "Innovation week" userc0 pj-member/role:general and others members between 0-150 of usersdx
    proj = await factories.create_project(
        workspace=ws_internal, name="Innovation week", created_by=created_by
    )
    projects.append(await factories.get_project_with_related_info(proj.id))
    general_role = await proj.roles.aget(slug="general")
    await factories.create_project_membership(
        project=proj, user=userc0, role=general_role
    )

    # for ws "Projects"
    # pj random-name members between 0-150 of usersdx
    proj = await factories.create_project(workspace=ws_projects, created_by=created_by)
    projects.append(await factories.get_project_with_related_info(proj.id))

    # 2 pj random-name userc0 pj-member/role:general and others members between 0-150 of usersdx
    for i in range(2):
        proj = await factories.create_project(
            workspace=ws_projects, created_by=created_by
        )
        projects.append(await factories.get_project_with_related_info(proj.id))
        general_role = await proj.roles.aget(slug="general")
        await factories.create_project_membership(
            project=proj, user=userc0, role=general_role
        )

    # for ws "Personal"
    # pj "TODO" with no other members
    proj = await factories.create_project(
        workspace=ws_personal, name="TODO", created_by=created_by
    )
    projects.append(await factories.get_project_with_related_info(proj.id))

    for project in projects:
        if project.name != "TODO":
            # PROJECT MEMBERSHIPS
            num_members = random.randint(0, 150)
            if num_members > 0:
                await factories.create_project_memberships(
                    project_id=project.id, users=usersdx[:num_members]
                )

            # PROJECT INVITATIONS
            await factories.create_project_invitations(project=project, users=usersdx)

        # STORIES
        await factories.create_stories(project_id=project.id, with_comments=True)


async def _create_scenario_manager_in_society_with_big_client() -> None:
    # USERS
    usere0 = await factories.create_user(username="usere0")
    userc0 = await users_repositories.get_user(filters={"username_or_email": "userc0"})
    if not userc0:
        raise Exception("User userc0 not found")
    usere1 = await factories.create_user(username="usere1")
    # usersex total 50
    usersex = [
        await factories.create_user(username=f"usere{i+1}") for i in range(1, 50)
    ]  # usere1 already exist
    created_by = usere0

    # WORKSPACES
    # member role is created by default
    # usere0 ws-member
    ws_random_name1 = await factories.create_workspace(created_by=created_by)
    ws_random_name2 = await factories.create_workspace(created_by=created_by)
    ws_random_name3 = await factories.create_workspace(created_by=created_by)
    ws_projects = await factories.create_workspace(
        created_by=created_by, name="Projects"
    )

    workspaces = [ws_random_name1, ws_random_name2, ws_random_name3, ws_projects]
    # ws with ws-members between 0-4 of usersex
    for ws in workspaces:
        num_ws_members = random.randint(0, 4)
        if num_ws_members > 0:
            await _create_workspace_memberships(
                workspace=ws, users=usersex[:num_ws_members]
            )

    # ws "Personal" with no other members
    ws_personal = await factories.create_workspace(
        created_by=created_by, name="Personal"
    )

    # PROJECTS
    # it applies a template and creates also admin and general roles
    # usere0 pj-admin
    projects = []

    # for ws random-name1
    # 2 pj random-name usere1 pj-member/role:general and others members between 0-50 of usersex
    for i in range(2):
        proj = await factories.create_project(
            workspace=ws_random_name1, created_by=created_by
        )
        projects.append(await factories.get_project_with_related_info(proj.id))
        general_role = await proj.roles.aget(slug="general")
        await factories.create_project_membership(
            project=proj, user=usere1, role=general_role
        )

    # for ws random-name2
    # pj random-name usere1 pj-member/role:general and others members between 0-50 of usersex
    proj = await factories.create_project(
        workspace=ws_random_name2, created_by=created_by
    )
    projects.append(await factories.get_project_with_related_info(proj.id))
    general_role = await proj.roles.aget(slug="general")
    await factories.create_project_membership(
        project=proj, user=usere1, role=general_role
    )

    # for ws random-name3
    # pj with members between 0-50 of usersex
    projects_names = [
        "The one that doesn’t start",
        "The bigger one",
        "The one that failed",
        "The other one",
        "That project",
    ]
    for pj_name in projects_names:
        proj = await factories.create_project(
            workspace=ws_random_name3, name=pj_name, created_by=created_by
        )
        projects.append(await factories.get_project_with_related_info(proj.id))

    # for ws "Projects"
    # 5 pj random-name members between 0-50 of usersex
    for i in range(5):
        proj = await factories.create_project(
            workspace=ws_projects, created_by=created_by
        )
        projects.append(await factories.get_project_with_related_info(proj.id))

    # for ws "Personal"
    # pj "Birthday party" userc0 pj-member/role:general
    proj = await factories.create_project(
        workspace=ws_personal, name="Birthday party", created_by=created_by
    )
    projects.append(await factories.get_project_with_related_info(proj.id))
    general_role = await proj.roles.aget(slug="general")
    await factories.create_project_membership(
        project=proj, user=userc0, role=general_role
    )

    # pj "TODO" with no other members
    proj = await factories.create_project(
        workspace=ws_personal, name="TODO", created_by=created_by
    )
    projects.append(await factories.get_project_with_related_info(proj.id))

    for project in projects:
        if project.workspace.name != "Personal":
            # PROJECT MEMBERSHIPS
            num_members = random.randint(0, 50)
            if num_members > 0:
                await factories.create_project_memberships(
                    project_id=project.id, users=usersex[:num_members]
                )

            # PROJECT INVITATIONS
            await factories.create_project_invitations(project=project, users=usersex)

        if project.name == "Birthday party":
            # PROJECT INVITATIONS
            await _create_accepted_project_invitations(project=project)

        # STORIES
        await factories.create_stories(project_id=project.id, with_comments=True)


async def _create_scenario_manager_in_society_with_own_product() -> None:
    # USERS
    userf0 = await users_repositories.get_user(filters={"username_or_email": "userf0"})
    if not userf0:
        raise Exception("User userf0 not found")
    userf1 = await factories.create_user(username="userf1")
    userf2 = await factories.create_user(username="userf2")
    userf3 = await factories.create_user(username="userf3")
    # usersfx total 40
    usersfx = [
        await factories.create_user(username=f"userf{i+1}") for i in range(3, 40)
    ]  # userf1, userf2, userf3 already exist
    created_by = userf0

    # WORKSPACES
    # member role is created by default
    # userf0 ws-member
    # ws "Projects" userf1, userf2 and userf3 ws-members
    ws_projects = await factories.create_workspace(
        created_by=created_by, name="Projects"
    )
    await _create_workspace_memberships(
        workspace=ws_projects, users=[userf1, userf2, userf3]
    )
    # ws "Personal" with no other members
    ws_personal = await factories.create_workspace(
        created_by=created_by, name="Personal"
    )

    # PROJECTS
    # it applies a template and creates also admin and general roles
    # userf0 pj-admin
    projects = []

    # for ws "Projects"
    # pj with members between 0-40 of usersfx
    projects_names = [
        "Our product - marketing",
        "Our product - growth",
        "Our product - research",
        "The old product",
        "Our product but mobile",
        "Onboarding",
        "Killer project (beta)",
        "The project that is already in production",
    ]
    for pj_name in projects_names:
        proj = await factories.create_project(
            workspace=ws_projects, name=pj_name, created_by=created_by
        )
        projects.append(await factories.get_project_with_related_info(proj.id))

    # for ws "Personal"
    # pj with no other members
    projects_names = ["Birthday party", "TODO"]
    for pj_name in projects_names:
        proj = await factories.create_project(
            workspace=ws_personal, name=pj_name, created_by=created_by
        )
        projects.append(await factories.get_project_with_related_info(proj.id))

    for project in projects:
        if project.workspace.name != "Personal":
            # PROJECT MEMBERSHIPS
            num_members = random.randint(0, 40)
            if num_members > 0:
                await factories.create_project_memberships(
                    project_id=project.id, users=usersfx[:num_members]
                )

            # PROJECT INVITATIONS
            await factories.create_project_invitations(project=project, users=usersfx)

        # STORIES
        await factories.create_stories(project_id=project.id, with_comments=True)


async def _create_scenario_manager_in_big_society_with_own_product() -> None:
    # USERS
    userg0 = await factories.create_user(username="userg0")
    # usersgx total 100
    usersgx = [
        await factories.create_user(username=f"userg{i+1}") for i in range(0, 100)
    ]

    created_by = userg0

    # WORKSPACES
    # member role is created by default
    # userg0 ws-member
    ws_inner = await factories.create_workspace(created_by=created_by, name="Inner")
    ws_marketing = await factories.create_workspace(
        created_by=created_by, name="Marketing & comms"
    )
    ws_support = await factories.create_workspace(created_by=created_by, name="Support")
    ws_events = await factories.create_workspace(created_by=created_by, name="Events")
    ws_mobile = await factories.create_workspace(
        created_by=created_by, name="Mobile app"
    )
    ws_desktop = await factories.create_workspace(
        created_by=created_by, name="Desktop app"
    )

    workspaces = [ws_inner, ws_marketing, ws_support, ws_events, ws_mobile, ws_desktop]
    # ws with ws-members between 1-9 of usersgx
    for ws in workspaces:
        num_ws_members = random.randint(1, 9)
        await _create_workspace_memberships(
            workspace=ws, users=usersgx[:num_ws_members]
        )

    # PROJECTS
    # it applies a template and creates also admin and general roles
    # userg0 pj-admin
    projects = []

    # for ws "Inner"
    # pj with members between 1-100 of usersgx
    projects_names = ["Human resources", "Innovation week", "Onboarding"]
    for pj_name in projects_names:
        proj = await factories.create_project(
            workspace=ws_inner, name=pj_name, created_by=created_by
        )
        projects.append(await factories.get_project_with_related_info(proj.id))

    # for ws "Events"
    # pj with members between 1-100 of usersgx
    projects_names = ["2023", "2022", "2021", "2020"]
    for pj_name in projects_names:
        proj = await factories.create_project(
            workspace=ws_events, name=pj_name, created_by=created_by
        )
        projects.append(await factories.get_project_with_related_info(proj.id))

    # for ws "Mobile app"
    # pj with members between 1-100 of usersgx
    projects_names = ["First idea that didn’t work", "Design"]
    for pj_name in projects_names:
        proj = await factories.create_project(
            workspace=ws_mobile, name=pj_name, created_by=created_by
        )
        projects.append(await factories.get_project_with_related_info(proj.id))

    # for ws "Desktop app"
    # pjs with members between 1-100 of usersgx
    projects_names = ["The old product", "Hardware", "Software", "Research", "Support"]
    for pj_name in projects_names:
        proj = await factories.create_project(
            workspace=ws_desktop, name=pj_name, created_by=created_by
        )
        projects.append(await factories.get_project_with_related_info(proj.id))

    for project in projects:
        # PROJECT MEMBERSHIPS
        num_members = random.randint(1, 100)
        await factories.create_project_memberships(
            project_id=project.id, users=usersgx[:num_members]
        )

        # PROJECT INVITATIONS
        await factories.create_project_invitations(project=project, users=usersgx)

        # STORIES
        await factories.create_stories(project_id=project.id, with_comments=True)


async def _create_workspace_memberships(
    workspace: Workspace, users: list[User]
) -> None:
    # get users except the creator of the workspace
    users = [u for u in users if u.id != workspace.created_by_id]

    # add ws members
    for user in users:
        await ws_memberships_repositories.create_workspace_membership(
            user=user, workspace=workspace
        )


async def _create_accepted_project_invitations(project: Project) -> None:
    # add accepted invitations for project memberships
    invitations = [
        ProjectInvitation(
            user=m.user,
            project=project,
            role=m.role,
            email=m.user.email,
            status=ProjectInvitationStatus.ACCEPTED,
            invited_by=project.created_by,
        )
        for m in project.memberships.all()
        if m.user_id != project.created_by_id
    ]

    # create invitations in bulk
    await pj_invitations_repositories.create_project_invitations(objs=invitations)
