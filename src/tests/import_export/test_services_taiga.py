# Copyright (C) 2026 BIRU
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

from pathlib import Path
from unittest.mock import patch

import pytest
from django.core.files.uploadedfile import UploadedFile
from django.test import override_settings

from import_export import services
from import_export.models import (
    ImportationStatus,
    ProjectImportation,
    ProjectImportationType,
)
from import_export.serializers import TaigaProjectImport
from import_export.services.taiga import (
    convert_to_tenzu_permissions,
    ensure_roles_unique_attributes,
    get_template_from_taiga_project,
)
from ninja_jwt.utils import aware_utcnow
from permissions.choices import ProjectPermissions
from projects.memberships.models import ProjectRole
from projects.projects.models import Project
from projects.projects.repositories import ProjectTemplateModel
from tests.utils import factories as f
from tests.utils.taskqueue import TestTasksQueueManager
from workflows.models import Workflow, WorkflowStatus


@pytest.mark.django_db
async def test_do_import_project_no_kanban(tqmanager: TestTasksQueueManager, caplog):
    workspace = await f.create_workspace()
    source_path = (
        Path(__file__).resolve().parent / "samples" / "export_from_taiga_no-kanban.json"
    )
    with open(source_path) as source_file:
        await services.import_project(
            user=workspace.created_by,
            workspace=workspace,
            origin_type=ProjectImportationType.TAIGA,
            source=UploadedFile(source_file),
        )
    assert len(tqmanager.pending_jobs) == 1
    await tqmanager.run_async()
    assert tqmanager.succeeded_jobs and not tqmanager.failed_jobs
    project = await Project.objects.aget()
    importation = await ProjectImportation.objects.select_related("project").aget()
    assert project.created_at.year == 2025
    assert importation.status == ImportationStatus.SUCCESS
    assert importation.project == project
    assert await Workflow.objects.acount() == 1
    assert await WorkflowStatus.objects.acount() == 7
    assert (
        await ProjectRole.objects.acount() == 9
    )  # 3 mandatory from Tenzu, 6 from import
    assert not caplog.records


@pytest.mark.django_db
@override_settings(**{"MAX_NUM_WORKFLOWS": 1})
async def test_do_import_project_complete(tqmanager: TestTasksQueueManager, caplog):
    workspace = await f.create_workspace()
    source_path = (
        Path(__file__).resolve().parent
        / "samples"
        / "export_from_taiga_project1_small.json"
    )
    with open(source_path) as source_file:
        await services.import_project(
            user=workspace.created_by,
            workspace=workspace,
            origin_type=ProjectImportationType.TAIGA,
            source=UploadedFile(source_file),
        )
    assert len(tqmanager.pending_jobs) == 1
    await tqmanager.run_async()
    assert tqmanager.succeeded_jobs and not tqmanager.failed_jobs
    project = await Project.objects.aget()
    importation = await ProjectImportation.objects.select_related("project").aget()
    assert project.created_at.year == 2025
    assert importation.status == ImportationStatus.ONGOING
    assert importation.project == project
    assert await Workflow.objects.acount() == 2
    assert await WorkflowStatus.objects.acount() == 7 * 2
    assert (
        await ProjectRole.objects.acount() == 9
    )  # 3 mandatory from Tenzu, 6 from import
    assert not caplog.records


def test_convert_to_tenzu_permissions():
    assert convert_to_tenzu_permissions([]) == []
    assert sorted(
        convert_to_tenzu_permissions(
            [
                "view_project",
                "view_milestones",
                "add_milestone",
                "modify_milestone",
                "delete_milestone",
                "view_epics",
                "add_epic",
                "modify_epic",
                "comment_epic",
                "delete_epic",
                "view_us",
                "add_us",
                "modify_us",
                "comment_us",
                "delete_us",
                "view_tasks",
                "add_task",
                "modify_task",
                "comment_task",
                "delete_task",
                "view_issues",
                "add_issue",
                "modify_issue",
                "comment_issue",
                "delete_issue",
                "view_wiki_pages",
                "add_wiki_page",
                "modify_wiki_page",
                "comment_wiki_page",
                "delete_wiki_page",
                "view_wiki_links",
                "add_wiki_link",
                "modify_wiki_link",
                "delete_wiki_link",
            ]
        )
    ) == sorted(
        [
            ProjectPermissions.VIEW_STORY,
            ProjectPermissions.CREATE_STORY,
            ProjectPermissions.MODIFY_STORY,
            ProjectPermissions.VIEW_COMMENT,
            ProjectPermissions.CREATE_MODIFY_DELETE_COMMENT,
            ProjectPermissions.DELETE_STORY,
        ]
    )


def test_ensure_roles_unique_attributes():
    tenzu_roles = []
    taiga_roles = []
    ensure_roles_unique_attributes(tenzu_roles, taiga_roles)
    assert tenzu_roles == taiga_roles == []

    tenzu_roles = [dict(name="", slug="")]
    taiga_roles = [dict(name="", slug="")]
    ensure_roles_unique_attributes(tenzu_roles, taiga_roles)
    assert tenzu_roles == [dict(name="", slug="")]
    assert taiga_roles == [dict(name="Taiga 1", slug="taiga-1")]

    tenzu_roles = [
        dict(name="Foo", slug="bar"),
        dict(name="Admin", slug="admin"),
        dict(name="Read-Only", slug="read-only"),
    ]
    taiga_roles = [
        dict(name="", slug=""),
        dict(name="Member", slug="member"),
        dict(name="Foo", slug="bar"),
        dict(name="Taiga Foo1", slug="taiga-bar1"),
    ]
    ensure_roles_unique_attributes(tenzu_roles, taiga_roles)
    assert tenzu_roles == [
        dict(name="Foo", slug="bar"),
        dict(name="Admin", slug="admin"),
        dict(name="Read-Only", slug="read-only"),
    ]
    assert taiga_roles == [
        dict(name="", slug=""),
        dict(name="Member", slug="member"),
        dict(name="Taiga Foo2", slug="taiga-bar2"),
        dict(name="Taiga Foo1", slug="taiga-bar1"),
    ]


async def test_get_template_from_taiga_project():
    with (
        patch(
            "import_export.services.taiga.projects_services", autospec=True
        ) as fake_projects_services,
    ):
        default_roles = [
            {
                "name": "Owner",
                "slug": "owner",
                "order": 1,
                "editable": False,
                "is_owner": True,
                "permissions": [ProjectPermissions.CREATE_MODIFY_DELETE_ROLE],
            },
            {
                "name": "Member",
                "slug": "member",
                "order": 2,
                "editable": True,
                "is_owner": False,
                "permissions": [ProjectPermissions.VIEW_STORY],
            },
        ]
        project_template = f.build_project_template(roles=default_roles)
        fake_projects_services._get_default_template.return_value = (
            ProjectTemplateModel.model_validate(project_template, from_attributes=True)
        )
        taiga_project = TaigaProjectImport(
            name="test",
            description="",
            created_date=aware_utcnow(),
            is_kanban_activated=True,
            roles=[],
            swimlanes=[],
            us_statuses=[],
        )
        template_model = await get_template_from_taiga_project(taiga_project)
        assert template_model == ProjectTemplateModel.model_construct(
            roles=[default_roles[0]],
            workflows=[{"slug": "main", "name": "Main", "order": 1}],
            workflow_statuses=[],
        )

        # noinspection PyTypeChecker
        taiga_project = TaigaProjectImport(
            name="test",
            description="",
            created_date=aware_utcnow(),
            is_kanban_activated=True,
            roles=[
                dict(
                    name="Owner",
                    slug="owner",
                    order=10,
                    computable=False,
                    permissions=["view_project", "modify_us"],
                )
            ],
            swimlanes=[dict(name="test", order=1), dict(name="test2", order=2)],
            us_statuses=[
                dict(
                    name="Now",
                    slug="now",
                    order=1,
                    is_closed=False,
                    color="#FFFFFF",
                    is_archived=False,
                    wip_limit=None,
                ),
                dict(
                    name="Later",
                    slug="later",
                    order=2,
                    is_closed=False,
                    color="#FFFFFF",
                    is_archived=False,
                    wip_limit=None,
                ),
                dict(
                    name="Never",
                    slug="never",
                    order=3,
                    is_closed=False,
                    color="#FFFFFF",
                    is_archived=False,
                    wip_limit=None,
                ),
            ],
        )
        template_model = await get_template_from_taiga_project(taiga_project)
        template_model.roles[1]["permissions"].sort()
        assert template_model == ProjectTemplateModel.model_construct(
            roles=[
                default_roles[0],
                dict(
                    name="Taiga Owner1",
                    slug="taiga-owner1",
                    order=10,
                    editable=True,
                    is_owner=False,
                    permissions=[
                        ProjectPermissions.MODIFY_STORY,
                        ProjectPermissions.VIEW_STORY,
                    ],
                ),
            ],
            workflows=[
                dict(name="test", slug="test", order=1),
                dict(name="test2", slug="test2", order=2),
            ],
            workflow_statuses=[
                dict(
                    name="Now",
                    order=1,
                    color=1,
                ),
                dict(
                    name="Later",
                    order=2,
                    color=2,
                ),
                dict(
                    name="Never",
                    order=3,
                    color=3,
                ),
            ],
        )
