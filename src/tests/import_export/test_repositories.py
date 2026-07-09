# Copyright (C) 2024-2026 BIRU
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

import pytest
from OpenSSL.rand import status
from procrastinate.contrib.django.models import ProcrastinateJob
from procrastinate.jobs import Status

from attachments.models import Attachment
from comments.models import Comment
from import_export import repositories
from import_export.models import (
    ImportationStatus,
    ProjectImportation,
    ProjectImportationType,
)
from import_export.tasks import import_taiga_project
from ninja_jwt.utils import aware_utcnow
from stories.assignments.models import StoryAssignment
from stories.stories.models import Story
from tests.utils import factories as f
from tests.utils.bad_params import NOT_EXISTING_UUID
from tests.utils.utils import async_django_capture_on_commit_callbacks

pytestmark = pytest.mark.django_db


##########################################################
# create_importation
##########################################################


async def test_create_importation():
    source_file = f.build_string_file()
    workspace = await f.create_workspace()
    user = await f.create_user()
    importation = await repositories.create_project_importation(
        user=user,
        workspace=workspace,
        origin_type=ProjectImportationType.TAIGA,
        source_file=source_file,
    )
    assert importation.source.name.endswith(source_file.name)
    assert importation.created_by_id == user.id
    assert importation.workspace_id == workspace.id
    assert importation.extra_data == {}
    return importation


##########################################################
# get_importation
##########################################################


async def test_get_importation_return_importation():
    importation = await f.create_project_importation(project=None)
    assert (
        await repositories.get_project_importation(
            project_importation_id=importation.id
        )
        == importation
    )


async def test_get_importation_not_exists():
    with pytest.raises(ProjectImportation.DoesNotExist):
        await repositories.get_project_importation(
            project_importation_id=NOT_EXISTING_UUID
        )


##########################################################
# update_project_importation
##########################################################


async def test_update_project_importation():
    importation = await f.create_project_importation(project=None)
    assert importation.modified_at is None
    importation = await repositories.update_project_importation(
        importation, {"status": ImportationStatus.SUCCESS}
    )
    assert importation.modified_at is not None
    assert importation.status == ImportationStatus.SUCCESS


##########################################################
# list_workspace_project_importations_for_user
##########################################################


async def test_list_workspace_project_importations_for_user() -> (
    list[ProjectImportation]
):
    workspace = await f.create_workspace()
    await f.create_project_importation(
        created_by=workspace.created_by, workspace=workspace, project=None
    )
    await f.create_project_importation(
        created_by=workspace.created_by,
        workspace=workspace,
        project=None,
        status=ImportationStatus.ONGOING,
    )
    await f.create_project_importation(
        created_by=workspace.created_by,
        workspace=workspace,
        project=None,
        status=ImportationStatus.PENDING,
    )
    await f.create_project_importation(
        created_by=workspace.created_by,
        workspace=workspace,
        project=None,
        status=ImportationStatus.ACTION_NEEDED,
    )
    await f.create_project_importation(
        created_by=workspace.created_by,
        workspace=workspace,
        project=None,
        status=ImportationStatus.FAILURE,
    )

    # excluded
    await f.create_project_importation(
        created_by=workspace.created_by,
        workspace=workspace,
        project=None,
        status=ImportationStatus.SUCCESS,
    )  # because success
    await f.create_project_importation(
        created_by=workspace.created_by, project=None
    )  # because other workspace
    other_user = await f.create_user()
    await f.create_project_importation(
        created_by=other_user, workspace=workspace, project=None
    )  # because other user
    assert (
        len(
            await repositories.list_workspace_project_importations_for_user(
                workspace, workspace.created_by
            )
        )
        == 5
    )


##########################################################
# delete_project_importation
##########################################################


async def test_delete_project_importation():
    project_importation = await f.create_project_importation(
        status=ImportationStatus.FAILURE, project=None
    )
    source_path = Path(project_importation.source.path)
    assert Path(source_path).exists()

    async with async_django_capture_on_commit_callbacks(execute=True):
        deleted = await repositories.delete_project_importation(
            project_importation=project_importation
        )
    assert deleted == 1
    assert not Path(source_path).exists()


@pytest.mark.db_task_queue_app
async def test_cancel_project_importation():
    project_importation = await f.create_project_importation(
        status=ImportationStatus.PENDING, project=None
    )
    assert not await ProcrastinateJob.objects.aexists()
    assert not await repositories.cancel_project_importation(project_importation)
    await import_taiga_project.defer_async(
        project_importation_id=project_importation.b64id,
    )
    assert (
        await ProcrastinateJob.objects.filter(
            status__in=[Status.TODO.value, Status.DOING.value]
        ).acount()
        == 1
    )
    assert await repositories.cancel_project_importation(project_importation)
    assert not await ProcrastinateJob.objects.filter(
        status__in=[Status.TODO.value, Status.DOING.value]
    ).aexists()
    assert (
        await ProcrastinateJob.objects.filter(
            status__in=[Status.ABORTED.value, Status.CANCELLED.value]
        ).acount()
        == 1
    )
    assert not await repositories.cancel_project_importation(project_importation)

    # create multiple, identical jobs to check that it does not cause any error
    for _ in range(2):
        await import_taiga_project.defer_async(
            project_importation_id=project_importation.b64id,
        )
    assert (
        await ProcrastinateJob.objects.filter(
            status__in=[Status.TODO.value, Status.DOING.value]
        ).acount()
        == 2
    )
    assert await repositories.cancel_project_importation(project_importation)
    assert not await ProcrastinateJob.objects.filter(
        status__in=[Status.TODO.value, Status.DOING.value]
    ).aexists()
    assert (
        await ProcrastinateJob.objects.filter(
            status__in=[Status.ABORTED.value, Status.CANCELLED.value]
        ).acount()
        == 3
    )
    assert not await repositories.cancel_project_importation(project_importation)


##########################################################
# backport previous users
##########################################################


async def test_sync_pending_objects():
    now = aware_utcnow()
    user = await f.create_user()

    story = await f.create_story()
    already_done_story = await f.create_story(created_by=user)

    other_assignment = await f.create_story_assignment()
    already_done_assignment = await f.create_story_assignment(user=user)

    attachment = await f.create_attachment(
        content_object=story,
    )
    already_done_attachment = await f.create_attachment(
        content_object=story, created_by=user
    )

    comment = await f.create_comment(
        content_object=story,
    )
    already_done_comment = await f.create_comment(content_object=story, created_by=user)

    deleted_comment = await f.create_comment(content_object=story, deleted_at=now)
    already_done_deleted_comment = await f.create_comment(
        content_object=story, deleted_at=now, deleted_by=user
    )
    wrong_state_deleted_comment = await f.create_comment(
        content_object=story, deleted_by=user
    )

    await repositories.sync_pending_objects(
        user_id=user.id,
        pending_invites={
            "role_id": NOT_EXISTING_UUID,
            "created_stories_ids": [story.id, already_done_story.id, NOT_EXISTING_UUID],
            "assigned_stories_ids": [
                story.id,
                other_assignment.story_id,
                already_done_assignment.story_id,
                NOT_EXISTING_UUID,
            ],
            "created_attachments_ids": [
                attachment.id,
                already_done_attachment.id,
                NOT_EXISTING_UUID,
            ],
            "created_comments_ids": [
                comment.id,
                already_done_comment.id,
                NOT_EXISTING_UUID,
            ],
            "deleted_comments_ids": [
                deleted_comment.id,
                already_done_deleted_comment.id,
                wrong_state_deleted_comment.id,
                NOT_EXISTING_UUID,
            ],
        },
    )
    assert (
        await Story.objects.filter(
            id__in=[story.id, already_done_story.id], created_by=user
        ).acount()
        == 2
    )
    assert (
        await StoryAssignment.objects.filter(
            story_id__in=[
                story.id,
                other_assignment.story_id,
                already_done_assignment.story_id,
            ],
            user=user,
        ).acount()
        == 3
    )
    assert (
        await Attachment.objects.filter(
            id__in=[attachment.id, already_done_attachment.id], created_by=user
        ).acount()
        == 2
    )
    assert (
        await Comment.objects.filter(
            id__in=[comment.id, already_done_comment.id], created_by=user
        ).acount()
        == 2
    )
    assert (
        await Comment.objects.filter(
            id__in=[
                deleted_comment.id,
                already_done_deleted_comment.id,
                wrong_state_deleted_comment.id,
            ],
            deleted_by=user,
        ).acount()
        == 3
    )
