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
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import orjson
import pytest
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import UploadedFile
from django.test import override_settings

from attachments.models import Attachment
from comments.models import Comment
from import_export import services
from import_export.models import (
    ImportationStatus,
    ProjectImportation,
    ProjectImportationPendingInvitation,
    ProjectImportationType,
)
from import_export.notifications import PROJECT_IMPORTATION_ACTION_NEEDED
from import_export.serializers import FullTaigaProjectImport
from import_export.serializers.taiga import (
    _TaigaAttachment,
    _TaigaFile,
    _TaigaHistory,
    _TaigaRole,
    _TaigaSwimlane,
    _TaigaSwimlaneUserStoryStatus,
    _TaigaUserStory,
    _TaigaUserStoryStatus,
)
from import_export.services.taiga import (
    ProjectImportationPendingObject,
    build_story_attachment_from_taiga,
    build_story_comment_from_taiga,
    bulk_create_all,
    convert_to_tenzu_permissions,
    do_import_taiga_single_story,
    do_import_taiga_stories,
    do_import_taiga_users,
    ensure_roles_unique_attributes,
    get_template_from_taiga_project,
    sync_project_ids_to_taiga_import,
)
from ninja_jwt.utils import aware_utcnow
from notifications.models import Notification
from permissions.choices import ProjectPermissions
from projects.memberships.models import ProjectRole
from projects.projects.models import Project
from projects.projects.repositories import ProjectTemplateModel
from stories.stories.models import Story
from tests.utils import factories as f
from tests.utils.bad_params import NOT_EXISTING_UUID
from tests.utils.taskqueue import TestTasksQueueManager
from tests.utils.utils import patch_db_transaction
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
    assert importation.status == ImportationStatus.ACTION_NEEDED
    assert importation.extra_data["progress_percentage"] == 100
    assert importation.project == project
    assert await Workflow.objects.acount() == 1
    assert await WorkflowStatus.objects.acount() == 7
    assert (
        await ProjectRole.objects.acount() == 9
    )  # 3 mandatory from Tenzu, 6 from import
    assert not await Story.objects.aexists()
    assert await Notification.objects.filter(
        type=PROJECT_IMPORTATION_ACTION_NEEDED
    ).aexists()
    assert not await Notification.objects.exclude(
        type=PROJECT_IMPORTATION_ACTION_NEEDED
    ).aexists()
    assert not caplog.records


@pytest.mark.django_db
@override_settings(
    **{"MAX_NUM_WORKFLOWS": 1, "MAX_UPLOAD_FILE_SIZE": 100 * 1024 * 1024}
)
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
    assert importation.status == ImportationStatus.ACTION_NEEDED
    assert importation.extra_data["progress_percentage"] == 100
    assert importation.project == project
    assert await Workflow.objects.acount() == 2
    assert await WorkflowStatus.objects.acount() == 7 * 2
    assert (
        await ProjectRole.objects.acount() == 9
    )  # 3 mandatory from Tenzu, 6 from import
    assert await Story.objects.acount() == 6
    assert await Attachment.objects.acount() == 4
    assert await Comment.objects.acount() == 2
    assert await Notification.objects.filter(
        type=PROJECT_IMPORTATION_ACTION_NEEDED
    ).aexists()
    assert not await Notification.objects.exclude(
        type=PROJECT_IMPORTATION_ACTION_NEEDED
    ).aexists()
    assert not caplog.records


@pytest.mark.django_db
@override_settings(**{"MAX_UPLOAD_FILE_SIZE": 1})
async def test_do_import_project_complete_with_warnings(
    tqmanager: TestTasksQueueManager, caplog
):
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
    assert await Story.objects.acount() == 6
    assert not await Attachment.objects.aexists()
    assert await Notification.objects.acount() == 5  # 4 warning + 1 action_needed
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
    old_to_new_mapping = ensure_roles_unique_attributes(tenzu_roles, taiga_roles)
    assert tenzu_roles == [dict(name="", slug="")]
    assert taiga_roles == [dict(name="Taiga 1", slug="taiga-1")]
    assert old_to_new_mapping == {"slug": {"": "taiga-1"}, "name": {"": "Taiga 1"}}

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
    old_to_new_mapping = ensure_roles_unique_attributes(tenzu_roles, taiga_roles)
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
    assert old_to_new_mapping == {
        "slug": {
            "": "",
            "member": "member",
            "bar": "taiga-bar2",
            "taiga-bar1": "taiga-bar1",
        },
        "name": {
            "": "",
            "Member": "Member",
            "Foo": "Taiga Foo2",
            "Taiga Foo1": "Taiga Foo1",
        },
    }


async def test_get_template_from_taiga_project():
    with (
        patch(
            "import_export.services.taiga.projects_services._get_default_template",
            new=AsyncMock(),
        ) as fake_get_default_template,
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
        fake_get_default_template.return_value = ProjectTemplateModel.model_validate(
            project_template, from_attributes=True
        )
        taiga_project = FullTaigaProjectImport.model_construct(
            name="test",
            description="",
            created_date=aware_utcnow(),
            is_kanban_activated=True,
            roles=[],
            swimlanes=[],
            us_statuses=[],
        )
        (
            template_model,
            roles_old_to_new_mapping,
        ) = await get_template_from_taiga_project(taiga_project)
        assert template_model == ProjectTemplateModel.model_construct(
            roles=[default_roles[0]],
            workflows=[{"slug": "main", "name": "Main", "order": 1}],
            workflow_statuses=[],
        )
        assert roles_old_to_new_mapping == {"slug": {}, "name": {}}

        # noinspection PyTypeChecker
        taiga_project = FullTaigaProjectImport.model_construct(
            name="test",
            description="",
            created_date=aware_utcnow(),
            is_kanban_activated=True,
            roles=[
                _TaigaRole(
                    name="Owner",
                    slug="owner",
                    order=10,
                    computable=False,
                    permissions=["view_project", "modify_us"],
                )
            ],
            swimlanes=[
                _TaigaSwimlane(name="test", order=1),
                _TaigaSwimlane(name="test2", order=2),
            ],
            us_statuses=[
                _TaigaUserStoryStatus(
                    name="Now",
                    slug="now",
                    order=1,
                    is_closed=False,
                    color="#FFFFFF",
                    is_archived=False,
                    wip_limit=None,
                ),
                _TaigaUserStoryStatus(
                    name="Later",
                    slug="later",
                    order=2,
                    is_closed=False,
                    color="#FFFFFF",
                    is_archived=False,
                    wip_limit=None,
                ),
                _TaigaUserStoryStatus(
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
        (
            template_model,
            roles_old_to_new_mapping,
        ) = await get_template_from_taiga_project(taiga_project)
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
        assert roles_old_to_new_mapping == {
            "slug": {"owner": "taiga-owner1"},
            "name": {"Owner": "Taiga Owner1"},
        }


async def test_sync_project_ids_to_taiga_import():
    statuses = [f.build_workflow_status(), f.build_workflow_status()]
    other_statuses = [
        f.build_workflow_status(name=statuses[0].name),
        f.build_workflow_status(name=statuses[1].name),
    ]
    workflows = [
        f.build_workflow(statuses=statuses),
        f.build_workflow(statuses=other_statuses),
    ]
    roles = [
        f.build_project_role(),
        f.build_project_role(name="Taiga Owner1", slug="taiga-owner1"),
    ]
    old_to_new_slug_mapping = {
        "owner": "taiga-owner1",
    }
    taiga_project = FullTaigaProjectImport.model_construct(
        name="test",
        description="",
        created_date=aware_utcnow(),
        is_kanban_activated=True,
        roles=[
            _TaigaRole(
                name="Owner",
                slug="owner",
                order=10,
                computable=False,
                permissions=["view_project", "modify_us"],
            )
        ],
        swimlanes=[
            _TaigaSwimlane(name=workflows[1].name, order=2),
            _TaigaSwimlane(
                name=workflows[0].name,
                order=1,
                statuses=[
                    _TaigaSwimlaneUserStoryStatus(
                        wip_limit=None, status=statuses[0].name
                    ),
                    _TaigaSwimlaneUserStoryStatus(wip_limit=2, status=statuses[1].name),
                ],
            ),
        ],
        us_statuses=[
            _TaigaUserStoryStatus(
                name=statuses[0].name,
                slug="",
                order=1,
                is_closed=False,
                color="#FFFFFF",
                is_archived=False,
                wip_limit=None,
            ),
            _TaigaUserStoryStatus(
                name=statuses[1].name,
                slug="",
                order=2,
                is_closed=False,
                color="#FFFFFF",
                is_archived=False,
                wip_limit=None,
            ),
        ],
    )

    await sync_project_ids_to_taiga_import(
        taiga_project, workflows, roles, old_to_new_slug_mapping
    )

    assert [role.tenzu_id for role in taiga_project.roles] == [roles[1].id]
    assert [swimlane.tenzu_id for swimlane in taiga_project.swimlanes] == [
        workflows[1].id,
        workflows[0].id,
    ]
    assert taiga_project.swimlanes[0].statuses is None
    assert [status.tenzu_id for status in taiga_project.swimlanes[1].statuses] == [
        statuses[0].id,
        statuses[1].id,
    ]
    assert [status.tenzu_ids for status in taiga_project.us_statuses] == [
        [statuses[0].id, other_statuses[0].id],
        [statuses[1].id, other_statuses[1].id],
    ]


async def test_do_import_taiga_stories(caplog):
    project_importation = f.build_project_importation()
    workflows = [
        f.build_workflow(
            statuses=[f.build_workflow_status(), f.build_workflow_status()]
        )
    ]
    now = aware_utcnow()
    taiga_attachment = _TaigaAttachment.model_construct(order=0, attached_file=None)
    event = _TaigaHistory.model_construct(comment="")
    taiga_import = FullTaigaProjectImport.model_construct(
        user_stories=[
            _TaigaUserStory.model_construct(status=None, ref=1, subject="Test invalid"),
            _TaigaUserStory.model_construct(
                assigned_to="1user@tenzu.test",
                assigned_users=["1user@tenzu.test", "2user@tenzu.test"],
                owner="1user@tenzu.test",
                subject="Test title1",
                description="",
                swimlane=None,
                status=workflows[0].statuses.all()[1].name,
                kanban_order=1,
                created_date=now,
                modified_date=None,
                version=1,
                attachments=[],
                history=[],
            ),
            _TaigaUserStory.model_construct(
                assigned_to="1user@tenzu.test",
                assigned_users=[
                    "2user@tenzu.test",
                    "1user@tenzu.test",
                    project_importation.created_by.email,
                ],
                owner=project_importation.created_by.email,
                subject="Test title2",
                description="*text* \nIn **markdown**\n#Title\n- and\n- a\n- list\n",
                swimlane=None,
                status=workflows[0].statuses.all()[1].name,
                kanban_order=10,
                created_date=now,
                modified_date=None,
                version=3,
                attachments=[taiga_attachment],
                history=[event],
            ),
        ]
    )
    with (
        patch(
            "import_export.services.taiga.bulk_create_all", autospec=True
        ) as fake_bulk_create_all,
        patch.object(ContentType.objects, "get_for_model", return_value=ContentType()),
        patch(
            "import_export.services.taiga.update_project_importation", autospec=True
        ) as fake_update_project_importation,
    ):
        await do_import_taiga_stories(
            project_importation,
            workflows,
            taiga_import,
            {},
        )

    assert len(caplog.records) == 1
    assert "Test invalid" in caplog.records[0].message

    fake_bulk_create_all.assert_awaited_once()
    fake_update_project_importation.assert_awaited()
    assert (
        fake_bulk_create_all.await_args.kwargs["project_importation"]
        == project_importation
    )
    assert len(fake_bulk_create_all.await_args.kwargs["stories_to_create"]) == 2

    assert all(
        getattr(fake_bulk_create_all.await_args.kwargs["stories_to_create"][0], key)
        == value
        for key, value in dict(
            title="Test title1",
            description=None,
            project_id=project_importation.project_id,
            workflow_id=workflows[0].id,
            status_id=workflows[0].statuses.all()[1].id,
            created_by_id=None,
            order=1,
            created_at=now,
            description_updated_at=None,
            version=1,
        ).items()
    )
    assert all(
        getattr(fake_bulk_create_all.await_args.kwargs["stories_to_create"][1], key)
        == value
        for key, value in dict(
            title="Test title2",
            project_id=project_importation.project_id,
            workflow_id=workflows[0].id,
            status_id=workflows[0].statuses.all()[1].id,
            created_by_id=project_importation.created_by_id,
            order=10,
            created_at=now,
            description_updated_at=None,
            version=3,
        ).items()
    )
    assert orjson.loads(
        fake_bulk_create_all.await_args.kwargs["stories_to_create"][1].description
    )
    assert fake_bulk_create_all.await_args.kwargs["stories_to_create"][
        1
    ].description_binary
    assert len(fake_bulk_create_all.await_args.kwargs["assignments_to_create"]) == 1
    assert len(fake_bulk_create_all.await_args.kwargs["attachments_to_create"]) == 0
    assert len(fake_bulk_create_all.await_args.kwargs["comments_to_create"]) == 0
    assert len(fake_bulk_create_all.await_args.kwargs["attachment_warnings"]) == 0
    # pending data
    assert (
        len(fake_bulk_create_all.await_args.kwargs["pending_data"]["created_stories"])
        == 1
    )
    assert (
        len(fake_bulk_create_all.await_args.kwargs["pending_data"]["assigned_stories"])
        == 4
    )
    assert (
        len(
            fake_bulk_create_all.await_args.kwargs["pending_data"][
                "created_attachments"
            ]
        )
        == 0
    )
    assert (
        len(fake_bulk_create_all.await_args.kwargs["pending_data"]["created_comments"])
        == 0
    )
    assert (
        len(fake_bulk_create_all.await_args.kwargs["pending_data"]["deleted_comments"])
        == 0
    )

    # ids
    assert taiga_import.user_stories[1].tenzu_id is not None
    assert taiga_import.user_stories[2].tenzu_id is not None
    assert taiga_attachment.tenzu_id is None
    assert event.tenzu_id is None


async def test_do_import_taiga_stories_multibatches():
    project_importation = f.build_project_importation()
    workflows = [
        f.build_workflow(
            statuses=[f.build_workflow_status(), f.build_workflow_status()]
        )
    ]
    now = aware_utcnow()
    taiga_import = FullTaigaProjectImport.model_construct(
        user_stories=[
            _TaigaUserStory.model_construct(
                assigned_to="1user@tenzu.test",
                assigned_users=["1user@tenzu.test", "2user@tenzu.test"],
                owner="1user@tenzu.test",
                subject="Test title1",
                description="",
                swimlane=None,
                status=workflows[0].statuses.all()[1].name,
                kanban_order=1,
                created_date=now,
                modified_date=None,
                version=1,
                attachments=[],
                history=[],
            ),
            _TaigaUserStory.model_construct(
                assigned_to="1user@tenzu.test",
                assigned_users=[
                    "1user@tenzu.test",
                    "2user@tenzu.test",
                    project_importation.created_by.email,
                ],
                owner=project_importation.created_by.email,
                subject="Test title2",
                description="*text* \nIn **markdown**\n#Title\n- and\n- a\n- list\n",
                swimlane=None,
                status=workflows[0].statuses.all()[1].name,
                kanban_order=10,
                created_date=now,
                modified_date=None,
                version=3,
                attachments=[],
                history=[],
            ),
        ]
    )
    with (
        patch(
            "import_export.services.taiga.bulk_create_all", autospec=True
        ) as fake_bulk_create_all,
        patch(
            "import_export.services.taiga.update_project_importation", autospec=True
        ) as fake_update_project_importation,
        patch.object(ContentType.objects, "get_for_model", return_value=ContentType()),
        patch(
            "import_export.services.taiga._IMPORTATION_BULK_SIZE",
            new=1,
        ),
    ):
        await do_import_taiga_stories(
            project_importation,
            workflows,
            taiga_import,
            {},
        )

    assert fake_bulk_create_all.await_count == 3
    fake_update_project_importation.assert_awaited()
    assert (
        fake_bulk_create_all.await_args.kwargs["project_importation"]
        == project_importation
    )
    assert len(fake_bulk_create_all.await_args.kwargs["stories_to_create"]) == 0

    # ids
    assert taiga_import.user_stories[0].tenzu_id is not None
    assert taiga_import.user_stories[1].tenzu_id is not None


async def test_do_import_taiga_single_story():
    project_importation = f.build_project_importation()
    now = aware_utcnow()
    attached_file = _TaigaFile.model_construct(
        data=b"some initial text data", name="path/test_file.png"
    )
    attachments = [
        _TaigaAttachment.model_construct(order=0, attached_file=None),
        _TaigaAttachment.model_construct(
            order=1,
            owner=project_importation.created_by.email,
            name="test_file1.png",
            attached_file=attached_file,
        ),
        _TaigaAttachment.model_construct(
            order=2,
            owner="1user@tenzu.test",
            name="test_file2.png",
            attached_file=attached_file,
        ),
    ]
    events = [
        _TaigaHistory.model_construct(comment=""),
        _TaigaHistory.model_construct(
            user=("1user@tenzu.test", ""),
            created_at=now,
            comment="Test comment1",
            delete_comment_date=None,
            delete_comment_user=None,
            edit_comment_date=now,
        ),
        _TaigaHistory.model_construct(
            user=(project_importation.created_by.email, ""),
            created_at=now,
            comment="Test comment2",
            delete_comment_date=now,
            delete_comment_user=("2user@tenzu.test", ""),
            edit_comment_date=None,
        ),
        _TaigaHistory.model_construct(
            user=None,
            created_at=now,
            comment="Test comment3",
            delete_comment_date=now,
            delete_comment_user=None,
            edit_comment_date=None,
        ),
    ]
    stories_to_create = []
    assignments_to_create = []
    attachments_to_create = []
    comments_to_create = []
    attachment_warnings = []
    pending_data = {
        "assigned_stories": [],
        "created_stories": [],
        "created_attachments": [],
        "created_comments": [],
        "deleted_comments": [],
    }
    taiga_story = _TaigaUserStory.model_construct(
        assigned_to="1user@tenzu.test",
        assigned_users=[
            "2user@tenzu.test",
            "1user@tenzu.test",
            project_importation.created_by.email,
        ],
        owner="1user@tenzu.test",
        subject="Test title1",
        description="",
        swimlane=None,
        status="Status name",
        kanban_order=10,
        created_date=now,
        modified_date=None,
        version=3,
        attachments=attachments,
        history=events,
    )
    with (
        patch.object(ContentType.objects, "get_for_model", return_value=ContentType()),
    ):
        await do_import_taiga_single_story(
            taiga_story=taiga_story,
            project_importation=project_importation,
            converter=MagicMock(convert=dummy_convert),
            workflow_id=NOT_EXISTING_UUID,
            status_id=NOT_EXISTING_UUID,
            stories_to_create=stories_to_create,
            assignments_to_create=assignments_to_create,
            attachments_to_create=attachments_to_create,
            comments_to_create=comments_to_create,
            attachment_warnings=attachment_warnings,
            pending_data=pending_data,
        )

    assert len(stories_to_create) == 1
    assert stories_to_create[0].title == "Test title1"
    assert len(assignments_to_create) == 1
    assert len(attachments_to_create) == 2
    assert len(comments_to_create) == 3
    assert len(attachment_warnings) == 0

    # pending created_stories
    assert len(pending_data["created_stories"]) == 1
    assert pending_data["created_stories"][0]["user_email"] == "1user@tenzu.test"
    assert isinstance(pending_data["created_stories"][0]["db_object"], Story)
    assert pending_data["created_stories"][0]["db_object"].title == "Test title1"

    # pending assigned_stories
    assert len(pending_data["assigned_stories"]) == 2
    assert {
        assigned["user_email"] for assigned in pending_data["assigned_stories"]
    } == {
        "2user@tenzu.test",
        "1user@tenzu.test",
    }  # use set for comparison because order is not guaranteed
    assert all(
        isinstance(assigned["db_object"], Story)
        for assigned in pending_data["assigned_stories"]
    )
    assert [
        assigned["db_object"].title for assigned in pending_data["assigned_stories"]
    ] == ["Test title1", "Test title1"]

    # pending created_attachments
    assert len(pending_data["created_attachments"]) == 1
    assert pending_data["created_attachments"][0]["user_email"] == "1user@tenzu.test"
    assert isinstance(pending_data["created_attachments"][0]["db_object"], Attachment)
    assert pending_data["created_attachments"][0]["db_object"].name == "test_file2.png"

    # pending created_comments
    assert len(pending_data["created_comments"]) == 1
    assert pending_data["created_comments"][0]["user_email"] == "1user@tenzu.test"
    assert isinstance(pending_data["created_comments"][0]["db_object"], Comment)
    assert pending_data["created_comments"][0]["db_object"].text == "[Test comment1]"

    # pending deleted_comments
    assert len(pending_data["deleted_comments"]) == 1
    assert pending_data["deleted_comments"][0]["user_email"] == "2user@tenzu.test"
    assert isinstance(pending_data["deleted_comments"][0]["db_object"], Comment)
    assert pending_data["deleted_comments"][0]["db_object"].text == ""

    # ids
    assert taiga_story.tenzu_id is not None
    assert attachments[0].tenzu_id is None
    assert events[0].tenzu_id is None
    assert all(attachment.tenzu_id is not None for attachment in attachments[1:])
    assert all(event.tenzu_id is not None for event in events[1:])


async def test_do_import_taiga_single_story_no_external_owner():
    project_importation = f.build_project_importation()
    now = aware_utcnow()
    stories_to_create = []
    assignments_to_create = []
    attachments_to_create = []
    comments_to_create = []
    attachment_warnings = []
    pending_data = {
        "assigned_stories": [],
        "created_stories": [],
        "created_attachments": [],
        "created_comments": [],
        "deleted_comments": [],
    }
    story = _TaigaUserStory.model_construct(
        assigned_to=None,
        assigned_users=[],
        owner=project_importation.created_by.email,
        subject="Test title1",
        description="",
        swimlane=None,
        status="Status name",
        kanban_order=10,
        created_date=now,
        modified_date=None,
        version=3,
        attachments=[],
        history=[],
    )
    await do_import_taiga_single_story(
        taiga_story=story,
        project_importation=project_importation,
        converter=MagicMock(convert=dummy_convert),
        workflow_id=NOT_EXISTING_UUID,
        status_id=NOT_EXISTING_UUID,
        stories_to_create=stories_to_create,
        assignments_to_create=assignments_to_create,
        attachments_to_create=attachments_to_create,
        comments_to_create=comments_to_create,
        attachment_warnings=attachment_warnings,
        pending_data=pending_data,
    )

    assert len(stories_to_create) == 1
    assert stories_to_create[0].title == "Test title1"
    assert not any(
        (
            assignments_to_create,
            attachments_to_create,
            comments_to_create,
            attachment_warnings,
            pending_data["created_stories"],
            pending_data["assigned_stories"],
            pending_data["created_attachments"],
            pending_data["created_comments"],
            pending_data["deleted_comments"],
        )
    )

    story.owner = None
    stories_to_create = []
    await do_import_taiga_single_story(
        taiga_story=story,
        project_importation=project_importation,
        converter=MagicMock(convert=dummy_convert),
        workflow_id=NOT_EXISTING_UUID,
        status_id=NOT_EXISTING_UUID,
        stories_to_create=stories_to_create,
        assignments_to_create=assignments_to_create,
        attachments_to_create=attachments_to_create,
        comments_to_create=comments_to_create,
        attachment_warnings=attachment_warnings,
        pending_data=pending_data,
    )

    assert len(stories_to_create) == 1
    assert stories_to_create[0].title == "Test title1"
    assert not any(
        (
            assignments_to_create,
            attachments_to_create,
            comments_to_create,
            attachment_warnings,
            pending_data["created_stories"],
            pending_data["assigned_stories"],
            pending_data["created_attachments"],
            pending_data["created_comments"],
            pending_data["deleted_comments"],
        )
    )

    # ids
    assert story.tenzu_id is not None


async def test_bulk_create_all(caplog):
    project_importation = f.build_project_importation()
    pending_invites = {
        "1user@tenzu.test": ProjectImportationPendingInvitation(
            role_id=NOT_EXISTING_UUID,
            deleted_comments_ids=[],
            assigned_stories_ids=[],
            created_comments_ids=[],
            created_stories_ids=[],
            created_attachments_ids=[],
        )
    }
    with patch_db_transaction():
        await bulk_create_all(
            project_importation=project_importation,
            stories_to_create=[],
            assignments_to_create=[],
            attachments_to_create=[],
            comments_to_create=[],
            attachment_warnings=[],
            pending_invites=pending_invites,
            pending_data={
                "deleted_comments": [
                    ProjectImportationPendingObject(
                        user_email="1user@tenzu.test",
                        db_object=Mock(id="deleted-comment1"),
                    )
                ],
                "assigned_stories": [
                    ProjectImportationPendingObject(
                        user_email="1user@tenzu.test",
                        db_object=Mock(id="assigned-story1"),
                    ),
                    ProjectImportationPendingObject(
                        user_email="2user@tenzu.test",
                        db_object=Mock(id="assigned-story2"),
                    ),
                    ProjectImportationPendingObject(
                        user_email="1user@tenzu.test",
                        db_object=Mock(id="assigned-story3"),
                    ),
                ],
                "created_comments": [],
                "created_stories": [],
                "created_attachments": [],
            },
        )
    assert len(caplog.records) == 1
    assert "2user@tenzu.test" in caplog.records[0].message
    assert len(pending_invites) == 1
    assert pending_invites["1user@tenzu.test"]["deleted_comments_ids"] == [
        "deleted-comment1"
    ]
    assert pending_invites["1user@tenzu.test"]["assigned_stories_ids"] == [
        "assigned-story1",
        "assigned-story3",
    ]
    assert not pending_invites["1user@tenzu.test"]["created_comments_ids"]
    assert not pending_invites["1user@tenzu.test"]["created_stories_ids"]
    assert not pending_invites["1user@tenzu.test"]["created_attachments_ids"]


async def test_build_story_attachment_from_taiga_ok():
    project_importation = f.build_project_importation()
    story = f.build_story()
    warnings = []
    taiga_attachment = _TaigaAttachment.model_construct(
        owner=project_importation.created_by.email,
        name="test_file.png",
        attached_file=_TaigaFile.model_construct(
            data=b"some initial text data", name="path/test_file.png"
        ),
    )

    with (
        patch.object(ContentType.objects, "get_for_model", return_value=ContentType()),
    ):
        attachment = build_story_attachment_from_taiga(
            project_importation, story, taiga_attachment, warnings
        )
        assert story == attachment.content_object
        assert project_importation.created_by == attachment.created_by

        taiga_attachment.owner = "1user@tenzu.test"

        attachment = build_story_attachment_from_taiga(
            project_importation, story, taiga_attachment, warnings
        )
        assert story == attachment.content_object
        assert attachment.created_by is None

    assert not warnings

    # ids
    assert taiga_attachment.tenzu_id is not None


@override_settings(**{"MAX_UPLOAD_FILE_SIZE": 0})
async def test_build_story_attachment_from_taiga_ko():
    project_importation = f.build_project_importation()
    story = f.build_story()
    warnings = []
    taiga_attachment = _TaigaAttachment.model_construct(
        owner="1user@tenzu.test",
        name="test_file.png",
        attached_file=None,
    )
    assert (
        build_story_attachment_from_taiga(
            project_importation, story, taiga_attachment, warnings
        )
        is None
    )

    taiga_attachment.attached_file = _TaigaFile.model_construct(
        data=b"some initial text data", name="path/test_file.png"
    )
    assert (
        build_story_attachment_from_taiga(
            project_importation, story, taiga_attachment, warnings
        )
        is None
    )
    assert warnings == [
        {
            "file_name": "test_file.png",
            "file_size": len(taiga_attachment.attached_file.data),
        }
    ]

    # ids
    assert taiga_attachment.tenzu_id is None


async def dummy_convert(input_data):
    return input_data["id"], b"", f"[{input_data['content']}]"


async def test_do_import_taiga_stories_comment_ok():
    project_importation = f.build_project_importation()
    story = f.build_story()
    now = aware_utcnow()
    taiga_comment = _TaigaHistory.model_construct(
        user=(project_importation.created_by.email, ""),
        created_at=now,
        comment="Test comment",
        delete_comment_date=None,
        delete_comment_user=None,
        edit_comment_date=now,
    )
    with patch.object(ContentType.objects, "get_for_model", return_value=ContentType()):
        comment, creator, deleter = await build_story_comment_from_taiga(
            MagicMock(convert=dummy_convert),
            project_importation,
            story,
            taiga_comment,
        )
    assert all(
        getattr(comment, key) == value
        for key, value in dict(
            text="[Test comment]",
            object_id=story.id,
            created_at=now,
            created_by_id=project_importation.created_by_id,
            deleted_at=None,
            deleted_by_id=None,
            modified_at=now,
        ).items()
    )
    assert creator == project_importation.created_by.email
    assert deleter is None

    # ids
    assert taiga_comment.tenzu_id is not None


@pytest.mark.parametrize(
    "user",
    [[], None, ["not-existing", ""]],
)
async def test_do_import_taiga_stories_comment_ok_no_user(user):
    project_importation = f.build_project_importation()
    story = f.build_story()
    now = aware_utcnow()
    taiga_comment = _TaigaHistory.model_construct(
        user=user,
        created_at=now,
        comment="Test comment",
        delete_comment_date=None,
        delete_comment_user=user,  # ignored if delete_comment_date is None
        edit_comment_date=None,
    )
    with patch.object(ContentType.objects, "get_for_model", return_value=ContentType()):
        comment, creator, deleter = await build_story_comment_from_taiga(
            MagicMock(convert=dummy_convert),
            project_importation,
            story,
            taiga_comment,
        )
    assert all(
        getattr(comment, key) == value
        for key, value in dict(
            text="[Test comment]",
            object_id=story.id,
            created_at=now,
            created_by_id=None,
            deleted_at=None,
            deleted_by_id=None,
            modified_at=None,
        ).items()
    )
    if user:
        assert creator == user[0]
    else:
        assert creator is None
    assert deleter is None

    # ids
    assert taiga_comment.tenzu_id is not None


async def test_do_import_taiga_stories_comment_ok_deleted():
    project_importation = f.build_project_importation()
    story = f.build_story()
    now = aware_utcnow()
    taiga_comment = _TaigaHistory.model_construct(
        user=None,
        created_at=now,
        comment="Test comment",
        delete_comment_date=now,
        delete_comment_user=(project_importation.created_by.email, ""),
        edit_comment_date=None,
    )
    with patch.object(ContentType.objects, "get_for_model", return_value=ContentType()):
        comment, creator, deleter = await build_story_comment_from_taiga(
            MagicMock(), project_importation, story, taiga_comment
        )
    assert all(
        getattr(comment, key) == value
        for key, value in dict(
            object_id=story.id,
            text="",
            created_at=now,
            created_by_id=None,
            deleted_at=now,
            deleted_by_id=project_importation.created_by_id,
            modified_at=None,
        ).items()
    )
    assert creator is None
    assert deleter == project_importation.created_by.email

    # ids
    assert taiga_comment.tenzu_id is not None


async def test_do_import_taiga_stories_comment_ko():
    project_importation = f.build_project_importation()
    story = f.build_story()
    taiga_comment = _TaigaHistory.model_construct(
        comment="",
    )
    assert (
        await build_story_comment_from_taiga(
            MagicMock(), project_importation, story, taiga_comment
        )
    )[0] is None

    # ids
    assert taiga_comment.tenzu_id is None


async def test_do_import_taiga_users_empty():
    project_importation = f.build_project_importation()
    taiga_project = FullTaigaProjectImport.model_construct(
        name="test",
        description="",
        created_date=aware_utcnow(),
        is_kanban_activated=True,
        roles=[],
        swimlanes=[],
        us_statuses=[],
    )
    project_roles = [
        Mock(is_owner=True, slug="owner", name="Owner", id="owner-id"),
        Mock(is_owner=False, slug="admin", name="Admin", id="admin-id"),
        Mock(
            is_owner=False,
            slug="readonly-member",
            name="Readonly-member",
            id="readonly-id",
        ),
    ]
    pending_invites = await do_import_taiga_users(
        project_importation=project_importation,
        taiga_project=taiga_project,
        roles=project_roles,
        roles_old_to_new_name_mapping={},
    )
    assert not pending_invites
    taiga_project.owner = project_importation.created_by.email
    pending_invites = await do_import_taiga_users(
        project_importation=project_importation,
        taiga_project=taiga_project,
        roles=project_roles,
        roles_old_to_new_name_mapping={},
    )
    assert not pending_invites


async def test_do_import_taiga_users_members():
    project_importation = f.build_project_importation()
    taiga_project = FullTaigaProjectImport.model_construct(
        name="test",
        description="",
        created_date=aware_utcnow(),
        is_kanban_activated=True,
        roles=[],
        swimlanes=[],
        us_statuses=[],
        owner="1user@tenzu.test",
        memberships=[
            Mock(email=None),
            Mock(email="1user@tenzu.test"),
            Mock(email=project_importation.created_by.email),
            Mock(email="2user@tenzu.test", is_admin=True),
            Mock(email="3user@tenzu.test", is_admin=False, role=None),
            Mock(email="4user@tenzu.test", is_admin=False, role="Member"),
            Mock(email="5user@tenzu.test", is_admin=False, role="Unknown"),
        ],
    )
    project_roles = [
        Mock(is_owner=True, slug="owner", id="owner-id"),
        Mock(is_owner=False, slug="admin", id="admin-id"),
        Mock(is_owner=False, slug="readonly-member", id="readonly-id"),
        Mock(is_owner=False, slug="taiga-member", id="member-id"),
    ]
    for role_mock, name in zip(
        project_roles, ("Owner", "Admin", "Readonly-member", "Taiga member")
    ):
        # we need this because name argument is consumed by the Mock construction otherwise
        # see https://docs.python.org/3/library/unittest.mock.html#mock-names-and-the-name-attribute
        role_mock.name = name

    pending_invites = await do_import_taiga_users(
        project_importation=project_importation,
        taiga_project=taiga_project,
        roles=project_roles,
        roles_old_to_new_name_mapping={"Member": "Taiga member"},
    )
    assert len(pending_invites) == 5
    assert list(pending_invites.keys()) == [
        "1user@tenzu.test",
        "2user@tenzu.test",
        "3user@tenzu.test",
        "4user@tenzu.test",
        "5user@tenzu.test",
    ]
    assert [invite["role_id"] for invite in pending_invites.values()] == [
        "owner-id",
        "admin-id",
        "readonly-id",
        "member-id",
        "readonly-id",
    ]
