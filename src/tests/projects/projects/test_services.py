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

import uuid
from unittest.mock import patch

import pytest

from projects.invitations.choices import ProjectInvitationStatus
from projects.projects import services
from projects.projects.services import exceptions as ex
from tests.utils import factories as f
from users.models import AnonymousUser
from workspaces.workspaces.serializers.nested import WorkspaceNestedSerializer

pytestmark = pytest.mark.django_db


async def test_get_landing_page_for_workflow():
    assert services.get_landing_page_for_workflow(None) == ""
    assert services.get_landing_page_for_workflow("slug-w") == "kanban/slug-w"


##########################################################
# create_project
##########################################################


async def test_create_project():
    workspace = f.build_workspace()

    with (
        patch("projects.projects.services._create_project") as fake_create_project,
        patch(
            "projects.projects.services.get_project_detail"
        ) as fake_get_project_detail,
    ):
        await services.create_project(
            workspace=workspace,
            name="n",
            description="d",
            color=2,
            created_by=workspace.created_by,
        )

        fake_create_project.assert_awaited_once()
        fake_get_project_detail.assert_awaited_once()


async def test_internal_create_project(project_template):
    workspace = f.build_workspace()

    with (
        patch(
            "projects.projects.services.projects_repositories", autospec=True
        ) as fake_project_repository,
        patch(
            "projects.projects.services.pj_roles_repositories", autospec=True
        ) as fake_pj_role_repository,
        patch(
            "projects.projects.services.pj_memberships_repositories", autospec=True
        ) as fake_pj_memberships_repository,
    ):
        fake_project_repository.create_project.return_value = await f.create_project(
            project_template
        )

        await services.create_project(
            workspace=workspace,
            name="n",
            description="d",
            color=2,
            created_by=workspace.created_by,
        )

        fake_project_repository.create_project.assert_awaited_once()
        fake_project_repository.get_project_template.assert_awaited_once()
        fake_pj_role_repository.get_project_role.assert_awaited_once()
        fake_pj_memberships_repository.create_project_membership.assert_awaited_once()


async def test_create_project_with_logo():
    workspace = f.build_workspace()
    project = f.build_project(workspace=workspace)
    role = f.build_project_role(project=project)

    logo = f.build_image_uploadfile()

    with (
        patch(
            "projects.projects.services.projects_repositories", autospec=True
        ) as fake_project_repository,
        patch(
            "projects.projects.services.pj_roles_repositories", autospec=True
        ) as fake_pj_roles_repository,
        patch("projects.projects.services.pj_memberships_repositories", autospec=True),
    ):
        fake_project_repository.create_project.return_value = project
        fake_pj_roles_repository.get_project_role.return_value = role

        await services._create_project(
            workspace=workspace,
            name="n",
            description="d",
            color=2,
            created_by=workspace.created_by,
            logo_file=logo,
        )

        service_file_param = fake_project_repository.create_project.call_args_list[0][1]
        assert service_file_param["logo"].name == logo.name
        assert service_file_param["logo"].file == logo.file


async def test_create_project_with_no_logo(project_template):
    workspace = f.build_workspace()

    with (
        patch(
            "projects.projects.services.projects_repositories", autospec=True
        ) as fake_project_repository,
        patch("projects.projects.services.pj_roles_repositories", autospec=True),
        patch("projects.projects.services.pj_memberships_repositories", autospec=True),
    ):
        fake_project_repository.get_project_template.return_value = project_template
        fake_project_repository.create_project.return_value = await f.create_project(
            project_template
        )
        await services._create_project(
            workspace=workspace,
            name="n",
            description="d",
            color=2,
            created_by=workspace.created_by,
        )

        fake_project_repository.create_project.assert_awaited_once_with(
            workspace=workspace,
            name="n",
            description="d",
            color=2,
            created_by=workspace.created_by,
            logo=None,
            landing_page="kanban/main",
        )


##########################################################
# list_workspace_projects_for_user
##########################################################


async def test_list_workspace_projects_for_a_ws_member():
    workspace = await f.create_workspace()

    with (
        patch(
            "projects.projects.services.projects_repositories", autospec=True
        ) as fake_projects_repo,
    ):
        await services.list_workspace_projects_for_user(
            workspace=workspace, user=workspace.created_by
        )
        fake_projects_repo.list_projects.assert_awaited_once_with(
            filters={"workspace_id": workspace.id},
            select_related=["workspace"],
        )


async def test_list_workspace_projects_not_for_a_ws_member():
    workspace = f.build_workspace()
    user = f.build_user()

    with (
        patch(
            "projects.projects.services.projects_repositories", autospec=True
        ) as fake_projects_repo,
    ):
        await services.list_workspace_projects_for_user(workspace=workspace, user=user)
        fake_projects_repo.list_projects.assert_awaited_once_with(
            filters={"workspace_id": workspace.id, "memberships__user_id": user.id},
            select_related=["workspace"],
        )


##########################################################
# get_workspace_invited_projects_for_user
##########################################################


async def test_list_workspace_invited_projects_for_user():
    workspace = f.build_workspace()

    with patch(
        "projects.projects.services.projects_repositories", autospec=True
    ) as fake_projects_repo:
        await services.list_workspace_invited_projects_for_user(
            workspace=workspace, user=workspace.created_by
        )
        fake_projects_repo.list_projects.assert_awaited_once_with(
            filters={
                "workspace_id": workspace.id,
                "invitations__user_id": workspace.created_by.id,
                "invitations__status": ProjectInvitationStatus.PENDING,
            }
        )


##########################################################
# get_project_detail
##########################################################


async def test_get_project_detail():
    workspace = await f.create_workspace()
    project = f.build_project(created_by=workspace.created_by, workspace=workspace)

    with (
        patch(
            "projects.projects.services.permissions_services", autospec=True
        ) as fake_permissions_services,
        patch(
            "projects.projects.services.workspaces_services", autospec=True
        ) as fake_workspaces_services,
        patch(
            "projects.projects.services.pj_invitations_services", autospec=True
        ) as fake_pj_invitations_services,
    ):
        fake_permissions_services.get_user_project_role_info.return_value = (
            True,
            True,
            [],
        )
        fake_permissions_services.get_user_permissions_for_project.return_value = []
        fake_permissions_services.is_workspace_member.return_value = True
        fake_pj_invitations_services.has_pending_project_invitation.return_value = True
        fake_workspaces_services.get_workspace_nested.return_value = (
            WorkspaceNestedSerializer(
                id=uuid.uuid1(), name="ws 1", slug="ws-1", user_role="admin"
            )
        )
        await services.get_project_detail(project=project, user=workspace.created_by)

        fake_permissions_services.get_user_project_role_info.assert_awaited_once_with(
            project=project, user=workspace.created_by
        )
        fake_permissions_services.get_user_permissions_for_project.assert_awaited_once_with(
            is_project_admin=True,
            is_workspace_member=True,
            is_project_member=True,
            is_authenticated=True,
            project_role_permissions=[],
            project=project,
        )
        fake_pj_invitations_services.has_pending_project_invitation.assert_awaited_once_with(
            user=workspace.created_by, project=project
        )
        fake_workspaces_services.get_workspace_nested.assert_awaited_once_with(
            workspace_id=workspace.id, user_id=workspace.created_by.id
        )


async def test_get_project_detail_anonymous():
    user = AnonymousUser()
    workspace = await f.create_workspace()
    permissions = ["modify_story", "view_story"]
    project = f.build_project(workspace=workspace, public_permissions=permissions)

    with (
        patch(
            "projects.projects.services.permissions_services", autospec=True
        ) as fake_permissions_services,
        patch(
            "projects.projects.services.workspaces_services", autospec=True
        ) as fake_workspaces_services,
        patch(
            "projects.projects.services.pj_invitations_services", autospec=True
        ) as fake_pj_invitations_services,
    ):
        fake_permissions_services.get_user_project_role_info.return_value = (
            True,
            True,
            [],
        )
        fake_permissions_services.get_user_permissions_for_project.return_value = []
        fake_permissions_services.is_workspace_member.return_value = True
        fake_pj_invitations_services.has_pending_project_invitation.return_value = False
        fake_workspaces_services.get_workspace_nested.return_value = (
            WorkspaceNestedSerializer(
                id=uuid.uuid1(), name="ws 1", slug="ws-1", user_role="admin"
            )
        )
        await services.get_project_detail(project=project, user=user)

        fake_permissions_services.get_user_project_role_info.assert_awaited_once_with(
            project=project, user=user
        )
        fake_permissions_services.get_user_permissions_for_project.assert_awaited_once_with(
            is_project_admin=True,
            is_workspace_member=True,
            is_project_member=True,
            is_authenticated=False,
            project_role_permissions=[],
            project=project,
        )
        fake_pj_invitations_services.has_pending_project_invitation.assert_not_awaited()
        fake_workspaces_services.get_workspace_nested.assert_awaited_once_with(
            workspace_id=workspace.id, user_id=user.id
        )


##########################################################
# update_project
##########################################################


async def test_update_project_ok(tqmanager):
    user = f.build_user()
    project = f.build_project()
    values = {"name": "new name", "description": ""}

    with (
        patch(
            "projects.projects.services.projects_repositories", autospec=True
        ) as fake_pj_repo,
        patch(
            "projects.projects.services.get_project_detail", autospec=True
        ) as fake_get_project_detail,
        patch(
            "projects.projects.services.projects_events", autospec=True
        ) as fake_projects_events,
    ):
        await services.update_project(project=project, updated_by=user, values=values)
        fake_pj_repo.update_project.assert_awaited_once_with(
            project=project, values=values
        )
        fake_updated_project = fake_pj_repo.update_project.return_value
        assert len(tqmanager.pending_jobs) == 0
        fake_get_project_detail.assert_awaited_once_with(
            project=fake_updated_project, user=user
        )
        fake_updated_project_detail = fake_get_project_detail.return_value
        fake_projects_events.emit_event_when_project_is_updated.assert_awaited_once_with(
            project_detail=fake_updated_project_detail,
            project_id=fake_updated_project.b64id,
            updated_by=user,
        )


async def test_update_project_ok_with_new_logo(tqmanager):
    user = f.build_user()
    new_logo = f.build_image_uploadfile()
    project = f.build_project()
    values = {"name": "new name", "description": "", "logo": new_logo}

    with (
        patch(
            "projects.projects.services.projects_repositories", autospec=True
        ) as fake_pj_repo,
        patch(
            "projects.projects.services.get_project_detail", autospec=True
        ) as fake_get_project_detail,
        patch(
            "projects.projects.services.projects_events", autospec=True
        ) as fake_projects_events,
    ):
        await services.update_project(project=project, updated_by=user, values=values)
        fake_pj_repo.update_project.assert_awaited_once_with(
            project=project, values=values
        )
        fake_updated_project = fake_pj_repo.update_project.return_value
        assert len(tqmanager.pending_jobs) == 0
        fake_get_project_detail.assert_awaited_once_with(
            project=fake_updated_project, user=user
        )
        fake_updated_project_detail = fake_get_project_detail.return_value
        fake_projects_events.emit_event_when_project_is_updated.assert_awaited_once_with(
            project_detail=fake_updated_project_detail,
            project_id=fake_updated_project.b64id,
            updated_by=user,
        )


async def test_update_project_ok_with_logo_replacement(tqmanager):
    user = f.build_user()
    logo = f.build_image_file()
    new_logo = f.build_image_uploadfile(name="new_logo")
    project = f.build_project(logo=logo)
    values = {"name": "new name", "description": "", "logo": new_logo}

    with (
        patch(
            "projects.projects.services.projects_repositories", autospec=True
        ) as fake_pj_repo,
        patch(
            "projects.projects.services.get_project_detail", autospec=True
        ) as fake_get_project_detail,
        patch(
            "projects.projects.services.projects_events", autospec=True
        ) as fake_projects_events,
    ):
        await services.update_project(project=project, updated_by=user, values=values)
        fake_pj_repo.update_project.assert_awaited_once_with(
            project=project, values=values
        )
        fake_updated_project = fake_pj_repo.update_project.return_value
        # assert len(tqmanager.pending_jobs) == 1
        # job = tqmanager.pending_jobs[0]
        # assert "delete_old_logo" in job["task_name"]
        # assert "path" in job["args"]
        # assert job["args"]["path"].endswith(logo.name)
        fake_get_project_detail.assert_awaited_once_with(
            project=fake_updated_project, user=user
        )
        fake_updated_project_detail = fake_get_project_detail.return_value
        fake_projects_events.emit_event_when_project_is_updated.assert_awaited_once_with(
            project_detail=fake_updated_project_detail,
            project_id=fake_updated_project.b64id,
            updated_by=user,
        )


async def test_update_project_name_empty(tqmanager):
    user = f.build_user()
    project = f.build_project()
    logo = f.build_image_file()
    values = {"name": "", "description": "", "logo": logo}

    with (
        patch(
            "projects.projects.services.projects_repositories", autospec=True
        ) as fake_pj_repo,
        patch(
            "projects.projects.services.get_project_detail", autospec=True
        ) as fake_get_project_detail,
        pytest.raises(ex.TenzuValidationError),
        patch(
            "projects.projects.services.projects_events", autospec=True
        ) as fake_projects_events,
    ):
        await services.update_project(project=project, updated_by=user, values=values)
        fake_pj_repo.update_project.assert_not_awaited()
        assert len(tqmanager.pending_jobs) == 0
        fake_get_project_detail.assert_not_awaited()
        fake_projects_events.emit_event_when_project_is_updated.assert_not_awaited()


##########################################################
# update_project_landing_page
##########################################################


async def test_update_project_landing_page_ok():
    user = f.build_user()
    project = f.build_project()
    values = {"landing_page": "kanban/new_slug"}

    with (
        patch(
            "projects.projects.services.projects_repositories", autospec=True
        ) as fake_pj_repo,
        patch(
            "projects.projects.services.get_project_detail", autospec=True
        ) as fake_get_project_detail,
        patch(
            "projects.projects.services.projects_events", autospec=True
        ) as fake_projects_events,
    ):
        fake_pj_repo.get_first_workflow_slug.return_value = None
        await services.update_project_landing_page(
            project=project, updated_by=user, new_slug="new_slug"
        )

        fake_pj_repo.get_first_workflow_slug.assert_not_awaited()
        fake_pj_repo.update_project.assert_awaited_once_with(
            project,
            values=values,
        )

        fake_updated_project = fake_pj_repo.update_project.return_value

        fake_updated_project_detail = fake_get_project_detail.return_value

        fake_projects_events.emit_event_when_project_is_updated.assert_awaited_once_with(
            project_detail=fake_updated_project_detail,
            project_id=fake_updated_project.b64id,
            updated_by=user,
        )


async def test_update_project_landing_page_ok_empty_value():
    user = f.build_user()
    project = f.build_project()
    values = {"landing_page": ""}

    with (
        patch(
            "projects.projects.services.projects_repositories", autospec=True
        ) as fake_pj_repo,
        patch(
            "projects.projects.services.get_project_detail", autospec=True
        ) as fake_get_project_detail,
        patch(
            "projects.projects.services.projects_events", autospec=True
        ) as fake_projects_events,
    ):
        fake_pj_repo.get_first_workflow_slug.return_value = None
        await services.update_project_landing_page(project=project, updated_by=user)

        fake_pj_repo.get_first_workflow_slug.assert_awaited_once_with(project=project)
        fake_pj_repo.update_project.assert_awaited_once_with(
            project,
            values=values,
        )
        fake_updated_project = fake_pj_repo.update_project.return_value
        fake_updated_project_detail = fake_get_project_detail.return_value

        fake_projects_events.emit_event_when_project_is_updated.assert_awaited_once_with(
            project_detail=fake_updated_project_detail,
            project_id=fake_updated_project.b64id,
            updated_by=user,
        )


async def test_update_project_landing_page_ok_new_slug():
    user = f.build_user()
    project = f.build_project()
    values = {"landing_page": "kanban/new-w"}

    with (
        patch(
            "projects.projects.services.projects_repositories", autospec=True
        ) as fake_pj_repo,
        patch(
            "projects.projects.services.get_project_detail", autospec=True
        ) as fake_get_project_detail,
        patch(
            "projects.projects.services.projects_events", autospec=True
        ) as fake_projects_events,
    ):
        fake_pj_repo.get_first_workflow_slug.return_value = "new-w"
        await services.update_project_landing_page(project=project, updated_by=user)

        fake_pj_repo.get_first_workflow_slug.assert_awaited_once_with(project=project)
        fake_pj_repo.update_project.assert_awaited_once_with(
            project,
            values=values,
        )
        fake_updated_project = fake_pj_repo.update_project.return_value

        fake_updated_project_detail = fake_get_project_detail.return_value

        fake_projects_events.emit_event_when_project_is_updated.assert_awaited_once_with(
            project_detail=fake_updated_project_detail,
            project_id=fake_updated_project.b64id,
            updated_by=user,
        )


##########################################################
# update_project_public_permissions
##########################################################


async def test_update_project_public_permissions_ok():
    project = f.build_project()
    permissions = ["modify_story", "view_story"]

    with (
        patch(
            "projects.projects.services.projects_repositories", autospec=True
        ) as fake_project_repository,
        patch(
            "projects.projects.services.projects_events", autospec=True
        ) as fake_projects_events,
    ):
        await services.update_project_public_permissions(
            project=project, permissions=permissions
        )
        fake_project_repository.update_project.assert_awaited_once_with(
            project=project, values={"public_permissions": permissions}
        )
        fake_projects_events.emit_event_when_project_permissions_are_updated.assert_awaited_with(
            project=project
        )


##########################################################
# delete_project
##########################################################


async def test_delete_project_fail():
    user = f.build_user()
    project = f.build_project()

    with (
        patch(
            "projects.projects.services.projects_repositories", autospec=True
        ) as fake_projects_repo,
        patch(
            "projects.projects.services.projects_events", autospec=True
        ) as fake_projects_events,
        patch(
            "projects.projects.services.users_services", autospec=True
        ) as fake_users_services,
    ):
        fake_projects_repo.delete_projects.return_value = 0
        fake_users_services.list_guests_in_workspace_for_project.return_value = []

        await services.delete_project(project=project, deleted_by=user)

        fake_projects_events.emit_event_when_project_is_deleted.assert_not_awaited()
        fake_projects_repo.delete_projects.assert_awaited_once_with(
            project_id=project.id,
        )


async def test_delete_project_ok(tqmanager):
    user = f.build_user()
    logo = f.build_image_file()
    project = f.build_project(logo=logo)

    with (
        patch(
            "projects.projects.services.projects_repositories", autospec=True
        ) as fake_projects_repo,
        patch(
            "projects.projects.services.projects_events", autospec=True
        ) as fake_projects_events,
        patch(
            "projects.projects.services.users_services", autospec=True
        ) as fake_users_services,
    ):
        fake_projects_repo.delete_projects.return_value = 1
        fake_users_services.list_guests_in_workspace_for_project.return_value = []

        await services.delete_project(project=project, deleted_by=user)
        fake_projects_events.emit_event_when_project_is_deleted.assert_awaited_once_with(
            workspace=project.workspace, project=project, deleted_by=user, guests=[]
        )
        fake_projects_repo.delete_projects.assert_awaited_once_with(
            project_id=project.id,
        )
        # assert len(tqmanager.pending_jobs) == 1
        # job = tqmanager.pending_jobs[0]
        # assert "delete_old_logo" in job["task_name"]
        # assert "path" in job["args"]
        # assert job["args"]["path"].endswith(logo.name)
