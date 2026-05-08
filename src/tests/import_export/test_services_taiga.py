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
from unittest.mock import call, patch

import pytest
from django.core.files.uploadedfile import UploadedFile
from django.test import override_settings

from attachments.models import Attachment
from comments.models import Comment
from import_export import services
from import_export.models import (
    ImportationStatus,
    ProjectImportation,
    ProjectImportationType,
)
from import_export.serializers import TaigaProjectImport
from import_export.serializers.taiga import (
    _TaigaAttachment,
    _TaigaFile,
    _TaigaHistory,
    _TaigaUserStory,
)
from import_export.services.taiga import (
    convert_to_tenzu_permissions,
    do_import_taiga_stories,
    do_import_taiga_stories_attachment,
    do_import_taiga_stories_comment,
    ensure_roles_unique_attributes,
    get_template_from_taiga_project,
)
from ninja_jwt.utils import aware_utcnow
from permissions.choices import ProjectPermissions
from projects.memberships.models import ProjectRole
from projects.projects.models import Project
from projects.projects.repositories import ProjectTemplateModel
from stories.stories.models import Story
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
    assert not await Story.objects.aexists()
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
    assert importation.status == ImportationStatus.SUCCESS
    assert importation.project == project
    assert await Workflow.objects.acount() == 2
    assert await WorkflowStatus.objects.acount() == 7 * 2
    assert (
        await ProjectRole.objects.acount() == 9
    )  # 3 mandatory from Tenzu, 6 from import
    assert await Story.objects.acount() == 6
    assert await Attachment.objects.acount() == 4
    assert await Comment.objects.acount() == 2
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


async def test_do_import_taiga_stories(caplog):
    project_importation = f.build_project_importation()
    workflows = [
        f.build_workflow(
            statuses=[f.build_workflow_status(), f.build_workflow_status()]
        )
    ]
    now = aware_utcnow()
    attachment = _TaigaAttachment.model_construct(order=0)
    event = _TaigaHistory.model_construct()
    with (
        patch(
            "import_export.services.taiga.stories_repositories", autospec=True
        ) as fake_stories_repositories,
        patch(
            "import_export.services.taiga.story_assignments_repositories", autospec=True
        ) as fake_story_assignments_repositories,
        patch(
            "import_export.services.taiga.do_import_taiga_stories_attachment",
            autospec=True,
        ) as fake_do_import_taiga_stories_attachment,
        patch(
            "import_export.services.taiga.do_import_taiga_stories_comment",
            autospec=True,
        ) as fake_do_import_taiga_stories_comment,
    ):
        await do_import_taiga_stories(
            project_importation,
            workflows,
            TaigaProjectImport.model_construct(
                user_stories=[
                    _TaigaUserStory.model_construct(
                        status=None, ref=1, subject="Test invalid"
                    ),
                    _TaigaUserStory.model_construct(
                        assigned_to="1user@tenzu.test",
                        assigned_users=["1user@tenzu.test", "2user@tenzu.test"],
                        owner="1user@tenzu.test",
                        subject="Test title1",
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
                        swimlane=None,
                        status=workflows[0].statuses.all()[1].name,
                        kanban_order=10,
                        created_date=now,
                        modified_date=None,
                        version=3,
                        attachments=[attachment],
                        history=[event],
                    ),
                ]
            ),
        )
        fake_stories_repositories.create_story.assert_has_awaits(
            [
                call(
                    title="Test title1",
                    description="",
                    project_id=project_importation.project_id,
                    workflow_id=workflows[0].id,
                    status_id=workflows[0].statuses.all()[1].id,
                    user_id=None,
                    order=1,
                    created_at=now,
                    description_updated_at=None,
                    version=1,
                ),
                call(
                    title="Test title2",
                    description="",
                    project_id=project_importation.project_id,
                    workflow_id=workflows[0].id,
                    status_id=workflows[0].statuses.all()[1].id,
                    user_id=project_importation.created_by_id,
                    order=10,
                    created_at=now,
                    description_updated_at=None,
                    version=3,
                ),
            ]
        )

    assert len(caplog.records) == 1
    assert "Test invalid" in caplog.records[0].message
    fake_story_assignments_repositories.create_story_assignment.assert_awaited_once_with(
        story=fake_stories_repositories.create_story.return_value,
        user=project_importation.created_by,
    )
    fake_do_import_taiga_stories_attachment.assert_awaited_once_with(
        project_importation,
        fake_stories_repositories.create_story.return_value,
        attachment,
    )
    fake_do_import_taiga_stories_comment.assert_awaited_once_with(
        project_importation,
        fake_stories_repositories.create_story.return_value,
        event,
    )


async def test_do_import_taiga_stories_attachment_ok():
    project_importation = f.build_project_importation()
    story = f.build_story()
    with (
        patch(
            "import_export.services.taiga.attachments_repositories", autospec=True
        ) as fake_attachments_repositories,
    ):
        attachment = _TaigaAttachment.model_construct(
            owner=project_importation.created_by.email,
            name="test_file.png",
            attached_file=_TaigaFile.model_construct(
                data=b"some initial text data", name="path/test_file.png"
            ),
        )
        await do_import_taiga_stories_attachment(project_importation, story, attachment)
        fake_attachments_repositories.create_attachment.assert_awaited_once()
        assert (
            story
            == fake_attachments_repositories.create_attachment.await_args.kwargs[
                "object"
            ]
        )
        assert (
            project_importation.created_by
            == fake_attachments_repositories.create_attachment.await_args.kwargs[
                "created_by"
            ]
        )

        attachment.owner = "1user@tenzu.test"
        fake_attachments_repositories.create_attachment.reset_mock()

        await do_import_taiga_stories_attachment(project_importation, story, attachment)
        fake_attachments_repositories.create_attachment.assert_awaited_once()
        assert (
            story
            == fake_attachments_repositories.create_attachment.await_args.kwargs[
                "object"
            ]
        )
        assert (
            fake_attachments_repositories.create_attachment.await_args.kwargs[
                "created_by"
            ]
            is None
        )


@override_settings(**{"MAX_UPLOAD_FILE_SIZE": 0})
async def test_do_import_taiga_stories_attachment_ko():
    project_importation = f.build_project_importation()
    story = f.build_story()
    with (
        patch(
            "import_export.services.taiga.notifications", autospec=True
        ) as fake_notifications,
    ):
        attachment = _TaigaAttachment.model_construct(
            owner="1user@tenzu.test",
            name="test_file.png",
            attached_file=None,
        )
        # next statement won't do anything, hence it won't trigger any DB operation
        await do_import_taiga_stories_attachment(project_importation, story, attachment)

        attachment.attached_file = _TaigaFile.model_construct(
            data=b"some initial text data", name="path/test_file.png"
        )
        await do_import_taiga_stories_attachment(project_importation, story, attachment)
        fake_notifications.notify_when_project_importation_file_too_big_warning.assert_awaited_once_with(
            project_importation, "test_file.png", len(attachment.attached_file.data)
        )


async def test_do_import_taiga_stories_comment_ok():
    project_importation = f.build_project_importation()
    story = f.build_story()
    now = aware_utcnow()
    with (
        patch(
            "import_export.services.taiga.comments_repositories", autospec=True
        ) as fake_comments_repositories,
    ):
        comment = _TaigaHistory.model_construct(
            user=(project_importation.created_by.email, ""),
            created_at=now,
            comment="Test comment",
            delete_comment_date=None,
            delete_comment_user=None,
            edit_comment_date=now,
        )
        await do_import_taiga_stories_comment(project_importation, story, comment)
        fake_comments_repositories.create_comment.assert_awaited_once_with(
            content_object=story,
            text="Test comment",
            created_at=now,
            created_by=project_importation.created_by,
            deleted_at=None,
            deleted_by=None,
            modified_at=now,
        )


@pytest.mark.parametrize(
    "user",
    [[], None, "not-existing"],
)
async def test_do_import_taiga_stories_comment_ok_no_user(user):
    project_importation = f.build_project_importation()
    story = f.build_story()
    now = aware_utcnow()
    with (
        patch(
            "import_export.services.taiga.comments_repositories", autospec=True
        ) as fake_comments_repositories,
    ):
        comment = _TaigaHistory.model_construct(
            user=user,
            created_at=now,
            comment="Test comment",
            delete_comment_date=None,
            delete_comment_user=None,
            edit_comment_date=None,
        )
        await do_import_taiga_stories_comment(project_importation, story, comment)
        fake_comments_repositories.create_comment.assert_awaited_once_with(
            content_object=story,
            text="Test comment",
            created_at=now,
            created_by=None,
            deleted_at=None,
            deleted_by=None,
            modified_at=None,
        )


async def test_do_import_taiga_stories_comment_ok_deleted():
    project_importation = f.build_project_importation()
    story = f.build_story()
    now = aware_utcnow()
    with (
        patch(
            "import_export.services.taiga.comments_repositories", autospec=True
        ) as fake_comments_repositories,
    ):
        comment = _TaigaHistory.model_construct(
            user=None,
            created_at=now,
            comment="Test comment",
            delete_comment_date=now,
            delete_comment_user=(project_importation.created_by.email, ""),
            edit_comment_date=None,
        )
        await do_import_taiga_stories_comment(project_importation, story, comment)
        fake_comments_repositories.create_comment.assert_awaited_once_with(
            content_object=story,
            text="",
            created_at=now,
            created_by=None,
            deleted_at=now,
            deleted_by=project_importation.created_by,
            modified_at=None,
        )


async def test_do_import_taiga_stories_comment_ko():
    project_importation = f.build_project_importation()
    story = f.build_story()
    comment = _TaigaHistory.model_construct(
        comment="",
    )
    # next statement won't do anything, hence it won't trigger any DB operation
    await do_import_taiga_stories_comment(project_importation, story, comment)
