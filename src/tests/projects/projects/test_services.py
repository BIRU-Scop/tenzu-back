# -*- coding: utf-8 -*-
# Copyright (C) 2024-2025 BIRU
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

from unittest.mock import patch

from permissions.choices import ProjectPermissions
from projects.projects import services
from tests.utils import factories as f
from tests.utils.utils import patch_db_transaction


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
        fake_get_project_detail.assert_awaited_once_with(
            project=fake_create_project.return_value, user=workspace.created_by
        )


async def test_internal_create_project():
    workspace = f.build_workspace()
    project = f.build_project(workspace=workspace)
    owner_role = f.build_project_role(project=project, is_owner=True)
    member_role = f.build_project_role(project=project, is_owner=False)

    with (
        patch(
            "projects.projects.services.projects_repositories", autospec=True
        ) as fake_project_repository,
        patch(
            "projects.projects.services.memberships_repositories", autospec=True
        ) as fake_memberships_repositories,
        patch("projects.projects.services.workflows_repositories", autospec=True),
        patch("projects.projects.services.ProjectDetailSerializer", autospec=True),
        patch_db_transaction(),
    ):
        fake_project_repository.create_project.return_value = project
        fake_project_repository.apply_template_to_project.return_value = [
            member_role,
            owner_role,
        ]

        await services.create_project(
            workspace=workspace,
            name="n",
            description="d",
            color=2,
            created_by=workspace.created_by,
        )

        fake_project_repository.create_project.assert_awaited_once()
        fake_project_repository.get_project_template.assert_awaited_once()
        assert workspace.created_by.project_role == owner_role
        fake_memberships_repositories.create_project_membership.assert_awaited_once_with(
            user=workspace.created_by, project=project, role=owner_role
        )


async def test_create_project_with_logo():
    workspace = f.build_workspace()
    project = f.build_project(workspace=workspace)
    owner_role = f.build_project_role(project=project, is_owner=True)

    logo = f.build_image_uploadfile()

    with (
        patch(
            "projects.projects.services.projects_repositories", autospec=True
        ) as fake_project_repository,
        patch(
            "projects.projects.services.memberships_repositories", autospec=True
        ) as fake_memberships_repositories,
        patch_db_transaction(),
    ):
        fake_project_repository.create_project.return_value = project
        fake_project_repository.apply_template_to_project.return_value = [
            owner_role,
        ]

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
        assert workspace.created_by.project_role == owner_role
        fake_memberships_repositories.create_project_membership.assert_awaited_once_with(
            user=workspace.created_by, project=project, role=owner_role
        )


async def test_create_project_with_no_logo():
    workspace = f.build_workspace()
    project = f.build_project(workspace=workspace)
    project_template = f.build_project_template()
    owner_role = f.build_project_role(project=project, is_owner=True)

    with (
        patch(
            "projects.projects.services.projects_repositories", autospec=True
        ) as fake_project_repository,
        patch(
            "projects.projects.services.memberships_repositories", autospec=True
        ) as fake_memberships_repositories,
        patch_db_transaction(),
    ):
        fake_project_repository.get_project_template.return_value = project_template
        fake_project_repository.create_project.return_value = project
        fake_project_repository.apply_template_to_project.return_value = [
            owner_role,
        ]
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
        assert workspace.created_by.project_role == owner_role
        fake_memberships_repositories.create_project_membership.assert_awaited_once_with(
            user=workspace.created_by, project=project, role=owner_role
        )


##########################################################
# list_workspace_projects_for_user
##########################################################


async def test_list_workspace_projects_for_a_ws_member():
    workspace = f.build_workspace()

    with (
        patch(
            "projects.projects.services.projects_repositories", autospec=True
        ) as fake_projects_repo,
    ):
        fake_projects_repo.list_workspace_projects_for_user.return_value = []
        await services.list_workspace_projects_for_user(
            workspace=workspace, user=workspace.created_by
        )
        fake_projects_repo.list_workspace_projects_for_user.assert_awaited_once_with(
            workspace=workspace, user=workspace.created_by
        )


##########################################################
# get_project_detail
##########################################################


async def test_get_project_detail():
    project = f.build_project()
    role = f.build_project_role(project=project, is_owner=True, permissions=[])
    workflow = f.build_workflow(project=project)

    with (
        patch(
            "projects.projects.services.workflows_repositories", autospec=True
        ) as fake_workflows_repositories,
        patch(
            "projects.projects.services.ProjectDetailSerializer", autospec=True
        ) as fake_ProjectDetailSerializer,
    ):
        # without membership's role
        await services.get_project_detail(project=project, user=project.created_by)
        fake_workflows_repositories.list_workflows_qs.assert_not_called()
        assert fake_ProjectDetailSerializer.call_args.kwargs["workflows"] == []
        assert fake_ProjectDetailSerializer.call_args.kwargs["user_role"] is None
        assert fake_ProjectDetailSerializer.call_args.kwargs["user_is_invited"] is False

        # with membership's role empty permissions
        project.created_by.project_role = role
        project.created_by.is_invited = False
        await services.get_project_detail(project=project, user=project.created_by)
        fake_workflows_repositories.list_workflows_qs.assert_not_called()
        assert fake_ProjectDetailSerializer.call_args.kwargs["workflows"] == []
        assert fake_ProjectDetailSerializer.call_args.kwargs["user_role"] == role
        assert fake_ProjectDetailSerializer.call_args.kwargs["user_is_invited"] is False

        # with membership's role ok permissions
        role = f.build_project_role(
            project=project,
            is_owner=True,
            permissions=[ProjectPermissions.VIEW_WORKFLOW],
        )
        project.created_by.project_role = role
        project.created_by.is_invited = True
        fake_workflows_repositories.list_workflows_qs.return_value.values.return_value.__aiter__.return_value = [
            workflow
        ]
        await services.get_project_detail(project=project, user=project.created_by)
        fake_workflows_repositories.list_workflows_qs.assert_called_once_with(
            filters={
                "project_id": project.id,
            }
        )
        assert fake_ProjectDetailSerializer.call_args.kwargs["workflows"] == [workflow]
        assert fake_ProjectDetailSerializer.call_args.kwargs["user_role"] == role
        assert fake_ProjectDetailSerializer.call_args.kwargs["user_is_invited"] is True


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
        assert len(tqmanager.pending_jobs) == 1
        job = tqmanager.pending_jobs[0]
        assert "delete_old_logo" in job["task_name"]
        assert "file_name" in job["args"]
        assert job["args"]["file_name"] == logo.name
        fake_get_project_detail.assert_awaited_once_with(
            project=fake_updated_project, user=user
        )
        fake_updated_project_detail = fake_get_project_detail.return_value
        fake_projects_events.emit_event_when_project_is_updated.assert_awaited_once_with(
            project_detail=fake_updated_project_detail,
            updated_by=user,
        )


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
            updated_by=user,
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
            "projects.projects.services.users_repositories", autospec=True
        ) as users_repositories,
        patch_db_transaction(),
    ):
        fake_projects_repo.delete_projects.return_value = 0

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
            "projects.projects.services.users_repositories", autospec=True
        ) as users_repositories,
        patch_db_transaction(),
    ):
        fake_projects_repo.delete_projects.return_value = 1

        await services.delete_project(project=project, deleted_by=user)
        fake_projects_events.emit_event_when_project_is_deleted.assert_awaited_once_with(
            workspace_id=project.workspace_id, project=project, deleted_by=user
        )
        fake_projects_repo.delete_projects.assert_awaited_once_with(
            project_id=project.id,
        )
        assert len(tqmanager.pending_jobs) == 1
        job = tqmanager.pending_jobs[0]
        assert "delete_old_logo" in job["task_name"]
        assert "file_name" in job["args"]
        assert job["args"]["file_name"] == logo.name
