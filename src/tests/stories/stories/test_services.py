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

from decimal import Decimal
from unittest.mock import patch

import pytest
from asgiref.sync import sync_to_async

from base.repositories.neighbors import Neighbor
from stories.stories import repositories, services
from stories.stories.services import exceptions as ex
from tests.utils import factories as f
from workflows.models import Workflow, WorkflowStatus
from workflows.serializers import WorkflowSerializer
from workflows.serializers.nested import WorkflowStatusNestedSerializer

#######################################################
# create_story
#######################################################


async def test_create_story_ok():
    user = f.build_user()
    status = f.build_workflow_status()
    story = f.build_story(status=status, workflow=status.workflow, assignee_ids=1)
    neighbors = Neighbor(next=f.build_story(), prev=f.build_story())

    with (
        patch(
            "stories.stories.services.stories_repositories", autospec=True
        ) as fake_stories_repo,
        patch(
            "stories.stories.services.workflows_repositories", autospec=True
        ) as fake_workflows_repo,
        patch(
            "stories.stories.services.stories_events", autospec=True
        ) as fake_stories_events,
        patch(
            "stories.stories.services.get_latest_story_order", autospec=True
        ) as fake_get_latest_story_order,
    ):
        fake_get_latest_story_order.return_value = None
        fake_workflows_repo.get_workflow_status.return_value = status
        fake_stories_repo.create_story.return_value = story
        fake_stories_repo.get_story.return_value = story
        fake_stories_repo.list_story_neighbors.return_value = neighbors

        complete_story = await services.create_story(
            project=story.project,
            workflow=status.workflow,
            title=story.title,
            description=story.description,
            status_id=status.id,
            user=user,
        )

        fake_stories_repo.create_story.assert_awaited_once_with(
            title=story.title,
            description=story.description,
            project_id=story.project.id,
            workflow_id=status.workflow.id,
            status_id=status.id,
            user_id=user.id,
            order=Decimal(100),
        )
        fake_workflows_repo.get_workflow_status.assert_awaited_once_with(
            status_id=status.id, filters={"workflow_id": status.workflow.id}
        )
        fake_get_latest_story_order.assert_awaited_once_with(status.id)
        fake_stories_events.emit_event_when_story_is_created.assert_awaited_once_with(
            project=story.project, story=complete_story
        )


async def test_create_story_invalid_status():
    user = f.build_user()
    story = f.build_story()

    with (
        pytest.raises(ex.InvalidStatusError),
        patch(
            "stories.stories.services.workflows_repositories", autospec=True
        ) as fake_workflows_repo,
    ):
        fake_workflows_repo.get_workflow_status.side_effect = (
            WorkflowStatus.DoesNotExist
        )
        await services.create_story(
            project=story.project,
            workflow=build_workflow_serializer(story),
            title=story.title,
            description=story.description,
            status_id="invalid_id",
            user=user,
        )


#######################################################
# list_paginated_stories
#######################################################


async def test_list_paginated_stories():
    fields = ["ref", "title", "workflow_id", "project_id", "status_id", "version"]
    with (
        patch(
            "stories.stories.services.stories_repositories", autospec=True
        ) as fake_stories_repo,
    ):
        story = f.build_story(assignees=1)
        fake_stories_repo.list_stories_qs.return_value.__aiter__.return_value = [story]

        await services.list_stories(
            project_id=story.project.id,
            workflow_slug=story.workflow.slug,
            offset=0,
            limit=10,
        )
        fake_stories_repo.list_stories_qs.assert_called_once_with(
            filters={
                "project_id": story.project.id,
                "workflow__slug": story.workflow.slug,
            },
            offset=0,
            limit=10,
            order_by=["order"],
        )
        fake_stories_repo.list_stories_qs.return_value.values.assert_called_once_with(
            *fields, assignee_ids=repositories.ASSIGNEE_IDS_ANNOTATION
        )
        fake_stories_repo.list_stories_qs.reset_mock()
        fake_stories_repo.list_stories_qs.return_value.values.reset_mock()
        story = f.build_story()
        fake_stories_repo.list_stories_qs.return_value.__aiter__.return_value = [story]
        await services.list_stories(
            project_id=story.project.id,
            workflow_slug=story.workflow.slug,
            offset=0,
            limit=10,
            get_assignees=False,
        )
        fake_stories_repo.list_stories_qs.assert_called_once_with(
            filters={
                "project_id": story.project.id,
                "workflow__slug": story.workflow.slug,
            },
            offset=0,
            limit=10,
            order_by=["order"],
        )
        fake_stories_repo.list_stories_qs.return_value.values.assert_called_once_with(
            *fields
        )


#######################################################
# get story
#######################################################


async def test_get_story_detail_ok():
    story1 = f.build_story(ref=1)
    story2 = f.build_story(
        ref=2,
        project=story1.project,
        workflow=story1.workflow,
        status=story1.status,
        assignee_ids=1,
    )
    story3 = f.build_story(
        ref=3, project=story1.project, workflow=story1.workflow, status=story1.status
    )
    neighbors = Neighbor(prev=story1, next=story3)

    with patch(
        "stories.stories.services.stories_repositories", autospec=True
    ) as fake_stories_repo:
        fake_stories_repo.get_story.return_value = story2
        fake_stories_repo.list_story_neighbors.return_value = neighbors

        story = await services.get_story_detail(
            project_id=story2.project_id, ref=story2.ref
        )

        fake_stories_repo.get_story.assert_awaited_once_with(
            ref=story2.ref,
            filters={"project_id": story2.project_id},
            select_related=[
                "created_by",
                "project",
                "workflow",
                "status",
                "project__workspace",
                "title_updated_by",
                "description_updated_by",
            ],
            get_assignees=True,
        )

        fake_stories_repo.list_story_neighbors.assert_awaited_once_with(
            story=story2, filters={"workflow_id": story2.workflow_id}
        )

        assert story.ref == story2.ref
        assert story.prev.ref == story1.ref
        assert story.next.ref == story3.ref


async def test_get_story_detail_no_neighbors():
    story1 = f.build_story(ref=1, assignee_ids=1)
    neighbors = Neighbor(prev=None, next=None)

    with patch(
        "stories.stories.services.stories_repositories", autospec=True
    ) as fake_stories_repo:
        fake_stories_repo.get_story.return_value = story1
        fake_stories_repo.list_story_neighbors.return_value = neighbors

        story = await services.get_story_detail(
            project_id=story1.project_id, ref=story1.ref
        )

        fake_stories_repo.get_story.assert_awaited_once_with(
            ref=story1.ref,
            filters={"project_id": story1.project_id},
            select_related=[
                "created_by",
                "project",
                "workflow",
                "status",
                "project__workspace",
                "title_updated_by",
                "description_updated_by",
            ],
            get_assignees=True,
        )

        fake_stories_repo.list_story_neighbors.assert_awaited_once_with(
            story=story1, filters={"workflow_id": story1.workflow_id}
        )

        assert story.ref == story1.ref
        assert story.prev is None
        assert story.next is None


#######################################################
# update_story
#######################################################


async def test_update_story_ok():
    user = f.build_user()
    story = f.build_story()
    values = {"title": "new title", "description": "new description"}
    detailed_story = {
        "ref": story.ref,
        "title": "new title",
        "description": "new description",
        "version": story.version + 1,
    }

    with (
        patch(
            "stories.stories.services.stories_repositories", autospec=True
        ) as fake_stories_repo,
        patch(
            "stories.stories.services._validate_and_process_values_to_update",
            autospec=True,
        ) as fake_validate_and_process,
        patch(
            "stories.stories.services.get_story_detail", autospec=True
        ) as fake_get_story_detail,
        patch(
            "stories.stories.services.stories_events", autospec=True
        ) as fake_stories_events,
        patch(
            "stories.stories.services.stories_notifications", autospec=True
        ) as fake_notifications,
    ):
        fake_validate_and_process.return_value = values
        fake_stories_repo.update_story.return_value = True
        fake_get_story_detail.return_value = detailed_story

        updated_story = await services.update_story(
            updated_by=user,
            story=story,
            current_version=story.version,
            values=values,
        )

        fake_validate_and_process.assert_awaited_once_with(
            story=story,
            values=values,
            updated_by=user,
        )
        fake_stories_repo.update_story.assert_awaited_once_with(
            id=story.id,
            current_version=story.version,
            values=values,
        )
        fake_get_story_detail.assert_awaited_once_with(
            project_id=story.project_id,
            ref=story.ref,
            neighbors=None,
        )
        fake_stories_events.emit_event_when_story_is_updated.assert_awaited_once_with(
            project=story.project,
            story=updated_story,
            updates_attrs=[*values],
        )
        fake_notifications.notify_when_story_status_change.assert_not_awaited()
        fake_notifications.notify_when_story_workflow_change.assert_not_awaited()

        assert updated_story == detailed_story


async def test_update_story_workflow_ok():
    user = f.build_user()
    project = f.build_project()
    old_workflow = f.build_workflow(project=project)
    workflow_status1 = f.build_workflow_status(workflow=old_workflow)
    workflow_status2 = f.build_workflow_status(workflow=old_workflow)
    story1 = f.build_story(
        project=project, workflow=old_workflow, status=workflow_status1
    )
    story2 = f.build_story(
        project=project, workflow=old_workflow, status=workflow_status1
    )
    story3 = f.build_story(
        project=project, workflow=old_workflow, status=workflow_status2
    )
    new_workflow = f.build_workflow(project=project)
    workflow_status3 = f.build_workflow_status(workflow=new_workflow)
    values = {
        "version": story2.version + 1,
        "workflow": new_workflow,
        "status": workflow_status3,
        "order": services.DEFAULT_ORDER_OFFSET + story2.order,
    }
    old_neighbors = {
        "prev": {"ref": story1.ref, "title": story1.title},
        "next": {"ref": story3.ref, "title": story3.title},
    }
    detailed_story = {
        "ref": story2.ref,
        "version": story2.version + 1,
        "workflow": {
            "id": new_workflow.id,
            "name": new_workflow.name,
            "slug": new_workflow.slug,
        },
        "prev": {"ref": story1.ref, "title": story1.title},
        "next": {"ref": story3.ref, "title": story3.title},
    }

    with (
        patch(
            "stories.stories.services.stories_repositories", autospec=True
        ) as fake_stories_repo,
        patch(
            "stories.stories.services._validate_and_process_values_to_update",
            autospec=True,
        ) as fake_validate_and_process,
        patch(
            "stories.stories.services.get_story_detail", autospec=True
        ) as fake_get_story_detail,
        patch(
            "stories.stories.services.stories_events", autospec=True
        ) as fake_stories_events,
        patch(
            "stories.stories.services.stories_notifications", autospec=True
        ) as fake_notifications,
    ):
        fake_validate_and_process.return_value = values
        fake_stories_repo.list_story_neighbors.return_value = old_neighbors
        fake_stories_repo.update_story.return_value = True
        fake_get_story_detail.return_value = detailed_story

        updated_story = await services.update_story(
            updated_by=user,
            story=story2,
            current_version=story2.version,
            values=values,
        )
        assert updated_story == detailed_story

        fake_validate_and_process.assert_awaited_once_with(
            story=story2,
            values=values,
            updated_by=user,
        )
        fake_stories_repo.update_story.assert_awaited_once_with(
            id=story2.id,
            current_version=story2.version,
            values=values,
        )
        fake_get_story_detail.assert_awaited_once_with(
            project_id=story2.project_id, ref=story2.ref, neighbors=old_neighbors
        )
        fake_stories_events.emit_event_when_story_is_updated.assert_awaited_once_with(
            project=story2.project,
            story=updated_story,
            updates_attrs=[*values],
        )

        fake_notifications.notify_when_story_status_change.assert_not_awaited()
        fake_notifications.notify_when_story_workflow_change.assert_awaited_once()


async def test_update_story_error_wrong_version():
    user = f.build_user()
    story = f.build_story()
    values = {"title": "new title"}

    with (
        patch(
            "stories.stories.services.stories_repositories", autospec=True
        ) as fake_stories_repo,
        patch(
            "stories.stories.services._validate_and_process_values_to_update",
            autospec=True,
        ) as fake_validate_and_process,
        patch(
            "stories.stories.services.get_story_detail", autospec=True
        ) as fake_get_story_detail,
        patch(
            "stories.stories.services.stories_events", autospec=True
        ) as fake_stories_events,
        patch(
            "stories.stories.services.stories_notifications", autospec=True
        ) as fake_notifications,
    ):
        fake_validate_and_process.return_value = values
        fake_stories_repo.update_story.return_value = False

        with pytest.raises(ex.UpdatingStoryWithWrongVersionError):
            await services.update_story(
                updated_by=user,
                story=story,
                current_version=story.version,
                values=values,
            )

        fake_validate_and_process.assert_awaited_once_with(
            story=story,
            values=values,
            updated_by=user,
        )
        fake_stories_repo.update_story.assert_awaited_once_with(
            id=story.id,
            current_version=story.version,
            values=values,
        )
        fake_get_story_detail.assert_not_awaited()
        fake_stories_events.emit_event_when_story_is_updated.assert_not_awaited()
        fake_notifications.notify_when_story_status_change.assert_not_awaited()
        fake_notifications.notify_when_story_workflow_change.assert_not_awaited()


#######################################################
# validate_and_process_values_to_update
#######################################################


async def test_validate_and_process_values_to_update_ok_without_status():
    user = f.build_user()
    story = f.build_story()
    values = {"title": "new title", "description": "new description"}

    with (
        patch(
            "stories.stories.services.stories_repositories", autospec=True
        ) as fake_stories_repo,
        patch(
            "stories.stories.services.workflows_repositories", autospec=True
        ) as fake_workflows_repo,
    ):
        valid_values = await services._validate_and_process_values_to_update(
            story=story, values=values, updated_by=user
        )

        fake_workflows_repo.get_workflow_status.assert_not_awaited()
        fake_stories_repo.list_stories_qs.assert_not_called()

        assert valid_values["title"] == values["title"]
        assert "title_updated_at" in valid_values
        assert "title_updated_by" in valid_values
        assert valid_values["description"] == values["description"]
        assert "description_updated_at" in valid_values
        assert "description_updated_by" in valid_values


async def test_validate_and_process_values_to_update_ok_with_status_empty():
    user = f.build_user()
    story = f.build_story()
    status = f.build_workflow_status()
    values = {
        "title": "new title",
        "description": "new description",
        "status_id": "",
    }

    with (
        patch(
            "stories.stories.services.stories_repositories", autospec=True
        ) as fake_stories_repo,
        patch(
            "stories.stories.services.workflows_repositories", autospec=True
        ) as fake_workflows_repo,
        patch(
            "stories.stories.services.get_latest_story_order", autospec=True
        ) as fake_get_latest_story_order,
    ):
        fake_get_latest_story_order.return_value = None
        fake_workflows_repo.get_workflow_status.return_value = status

        valid_values = await services._validate_and_process_values_to_update(
            story=story, values=values, updated_by=user
        )

        fake_workflows_repo.get_workflow_status.assert_not_awaited()
        fake_get_latest_story_order.assert_not_awaited()

        assert valid_values["title"] == values["title"]
        assert "title_updated_at" in valid_values
        assert "title_updated_by" in valid_values
        assert valid_values["description"] == values["description"]
        assert "description_updated_at" in valid_values
        assert "description_updated_by" in valid_values
        assert "status" not in valid_values


async def test_validate_and_process_values_to_update_ok_with_status_not_empty():
    user = f.build_user()
    story = f.build_story()
    status = f.build_workflow_status()
    story2 = f.build_story(status=status, order=42)
    values = {
        "title": "new title",
        "description": "new description",
        "status_id": status.id,
    }

    with (
        patch(
            "stories.stories.services.stories_repositories", autospec=True
        ) as fake_stories_repo,
        patch(
            "stories.stories.services.workflows_repositories", autospec=True
        ) as fake_workflows_repo,
        patch(
            "stories.stories.services.get_latest_story_order", autospec=True
        ) as fake_get_latest_story_order,
    ):
        fake_get_latest_story_order.return_value = story2.order
        fake_workflows_repo.get_workflow_status.return_value = status

        valid_values = await services._validate_and_process_values_to_update(
            story=story, values=values, updated_by=user
        )

        fake_workflows_repo.get_workflow_status.assert_awaited_once_with(
            status_id=values["status_id"],
            filters={
                "workflow_id": story.workflow_id,
            },
        )
        fake_get_latest_story_order.assert_awaited_once_with(status.id)

        assert valid_values["title"] == values["title"]
        assert "title_updated_at" in valid_values
        assert "title_updated_by" in valid_values
        assert valid_values["description"] == values["description"]
        assert "description_updated_at" in valid_values
        assert "description_updated_by" in valid_values
        assert valid_values["status"] == status
        assert valid_values["order"] == services.DEFAULT_ORDER_OFFSET + story2.order


async def test_validate_and_process_values_to_update_ok_with_same_status():
    user = f.build_user()
    status = f.build_workflow_status()
    story = f.build_story(status=status)
    values = {
        "title": "new title",
        "description": "new description",
        "status_id": status.id,
    }

    with (
        patch(
            "stories.stories.services.stories_repositories", autospec=True
        ) as fake_stories_repo,
        patch(
            "stories.stories.services.workflows_repositories", autospec=True
        ) as fake_workflows_repo,
    ):
        fake_workflows_repo.get_workflow_status.return_value = status

        valid_values = await services._validate_and_process_values_to_update(
            story=story, values=values, updated_by=user
        )

        fake_workflows_repo.get_workflow_status.assert_awaited_once_with(
            status_id=values["status_id"],
            filters={"workflow_id": story.workflow_id},
        )
        fake_stories_repo.list_stories_qs.assert_not_called()

        assert valid_values["title"] == values["title"]
        assert "title_updated_at" in valid_values
        assert "title_updated_by" in valid_values
        assert valid_values["description"] == values["description"]
        assert "description_updated_at" in valid_values
        assert "description_updated_by" in valid_values
        assert "status" not in valid_values
        assert "order" not in valid_values


async def test_validate_and_process_values_to_update_error_wrong_status():
    user = f.build_user()
    story = f.build_story()
    values = {
        "title": "new title",
        "description": "new description",
        "status_id": "wrong_status",
    }

    with (
        patch(
            "stories.stories.services.stories_repositories", autospec=True
        ) as fake_stories_repo,
        patch(
            "stories.stories.services.workflows_repositories", autospec=True
        ) as fake_workflows_repo,
    ):
        fake_workflows_repo.get_workflow_status.side_effect = (
            WorkflowStatus.DoesNotExist
        )

        with pytest.raises(ex.InvalidStatusError):
            await services._validate_and_process_values_to_update(
                story=story, values=values, updated_by=user
            )

        fake_workflows_repo.get_workflow_status.assert_awaited_once_with(
            status_id="wrong_status",
            filters={"workflow_id": story.workflow_id},
        )
        fake_stories_repo.list_stories_qs.assert_not_called()


async def test_validate_and_process_values_to_update_ok_with_workflow():
    user = f.build_user()
    project = f.build_project()
    workflow1 = f.build_workflow(project=project)
    status1 = f.build_workflow_status(workflow=workflow1)
    story1 = f.build_story(project=project, workflow=workflow1, status=status1)
    status2 = f.build_workflow_status()
    workflow2 = f.build_workflow(project=project, statuses=[status2])
    _ = f.build_workflow_status(workflow=workflow2)
    story2 = f.build_story(project=project, workflow=workflow2, status=status2)
    values = {"version": story1.version, "workflow_slug": workflow2.slug}

    with (
        patch(
            "stories.stories.services.stories_repositories", autospec=True
        ) as fake_stories_repo,
        patch(
            "stories.stories.services.workflows_repositories", autospec=True
        ) as fake_workflows_repo,
        patch(
            "stories.stories.services.get_latest_story_order", autospec=True
        ) as fake_get_latest_story_order,
    ):
        fake_get_latest_story_order.return_value = story2.order
        fake_workflows_repo.get_workflow.return_value = workflow2

        valid_values = await services._validate_and_process_values_to_update(
            story=story1, values=values, updated_by=user
        )

        fake_workflows_repo.get_workflow.assert_awaited_once_with(
            filters={"project_id": story1.project_id, "slug": workflow2.slug},
            prefetch_related=["statuses"],
        )
        fake_workflows_repo.list_workflow_statuses.assert_not_awaited()
        fake_get_latest_story_order.assert_awaited_once_with(status2.id)

        assert valid_values["workflow"] == workflow2
        assert valid_values["order"] == services.DEFAULT_ORDER_OFFSET + story2.order


async def test_validate_and_process_values_to_update_ok_with_workflow_empty():
    user = f.build_user()
    story = f.build_story()
    status = f.build_workflow_status()
    story2 = f.build_story(status=status, order=42)
    values = {
        "title": "new title",
        "description": "new description",
        "status_id": status.id,
        "workflow_slug": "",
    }

    with (
        patch(
            "stories.stories.services.stories_repositories", autospec=True
        ) as fake_stories_repo,
        patch(
            "stories.stories.services.workflows_repositories", autospec=True
        ) as fake_workflows_repo,
        patch(
            "stories.stories.services.get_latest_story_order", autospec=True
        ) as fake_get_latest_story_order,
    ):
        fake_get_latest_story_order.return_value = story2.order
        fake_workflows_repo.get_workflow_status.return_value = status

        valid_values = await services._validate_and_process_values_to_update(
            story=story, values=values, updated_by=user
        )

        fake_workflows_repo.get_workflow_status.assert_awaited_once_with(
            status_id=values["status_id"],
            filters={"workflow_id": story.workflow_id},
        )
        fake_get_latest_story_order.assert_awaited_once_with(status.id)
        fake_workflows_repo.get_workflow.assert_not_awaited()

        assert valid_values["title"] == values["title"]
        assert "title_updated_at" in valid_values
        assert "title_updated_by" in valid_values
        assert valid_values["description"] == values["description"]
        assert "description_updated_at" in valid_values
        assert "description_updated_by" in valid_values
        assert valid_values["status"] == status
        assert valid_values["order"] == services.DEFAULT_ORDER_OFFSET + story2.order


async def test_validate_and_process_values_to_update_error_wrong_workflow():
    user = f.build_user()
    story = f.build_story()
    values = {"version": story.version, "workflow_slug": "wrong_workflow"}

    with (
        patch(
            "stories.stories.services.stories_repositories", autospec=True
        ) as fake_stories_repo,
        patch(
            "stories.stories.services.workflows_repositories", autospec=True
        ) as fake_workflows_repo,
    ):
        fake_workflows_repo.get_workflow.side_effect = Workflow.DoesNotExist

        with pytest.raises(ex.InvalidWorkflowError):
            await services._validate_and_process_values_to_update(
                story=story, values=values, updated_by=user
            )

        fake_workflows_repo.get_workflow.assert_awaited_once_with(
            filters={"project_id": story.project_id, "slug": "wrong_workflow"},
            prefetch_related=["statuses"],
        )
        fake_stories_repo.list_stories_qs.assert_not_called()


async def test_validate_and_process_values_to_update_error_workflow_without_statuses():
    user = f.build_user()
    project = f.build_project()
    workflow1 = f.build_workflow(project=project)
    status1 = f.build_workflow_status(workflow=workflow1)
    story = f.build_story(project=project, workflow=workflow1, status=status1)
    workflow2 = f.build_workflow(project=project, statuses=[])
    values = {"version": story.version, "workflow_slug": workflow2.slug}

    with (
        patch(
            "stories.stories.services.stories_repositories", autospec=True
        ) as fake_stories_repo,
        patch(
            "stories.stories.services.workflows_repositories", autospec=True
        ) as fake_workflows_repo,
    ):
        fake_workflows_repo.get_workflow.return_value = workflow2

        with pytest.raises(ex.WorkflowHasNotStatusesError):
            await services._validate_and_process_values_to_update(
                story=story, values=values, updated_by=user
            )

        fake_workflows_repo.get_workflow.assert_awaited_once_with(
            filters={"project_id": story.project_id, "slug": workflow2.slug},
            prefetch_related=["statuses"],
        )
        fake_workflows_repo.list_workflow_statuses.assert_not_awaited()
        fake_stories_repo.list_stories_qs.assert_not_called()


async def test_validate_and_process_values_to_update_error_workflow_and_status():
    user = f.build_user()
    project = f.build_project()
    workflow1 = f.build_workflow(project=project)
    status1 = f.build_workflow_status(workflow=workflow1)
    story = f.build_story(project=project, workflow=workflow1, status=status1)
    workflow2 = f.build_workflow(project=project, statuses=None)
    values = {
        "version": story.version,
        "status_id": status1,
        "workflow_slug": workflow2.slug,
    }

    with (
        patch(
            "stories.stories.services.workflows_repositories", autospec=True
        ) as fake_workflows_repo,
    ):
        fake_workflows_repo.get_workflow_status.return_value = workflow2

        with pytest.raises(ex.InvalidStatusError):
            await services._validate_and_process_values_to_update(
                story=story, values=values, updated_by=user
            )


#######################################################
# _calculate_offset
#######################################################


async def test_calculate_offset() -> None:
    target_status = f.build_workflow_status()
    with (
        patch(
            "stories.stories.services.stories_repositories", autospec=True
        ) as fake_stories_repo,
        patch(
            "stories.stories.services.get_latest_story_order", autospec=True
        ) as fake_get_latest_story_order,
    ):
        # No reorder
        latest_story = f.build_story(status=target_status, order=36)
        fake_get_latest_story_order.return_value = latest_story.order
        offset, pre_order = await services._calculate_offset(
            total_stories_to_reorder=1, target_status=target_status
        )
        assert pre_order == latest_story.order
        assert offset == 100

        fake_get_latest_story_order.return_value = None
        offset, pre_order = await services._calculate_offset(
            total_stories_to_reorder=1, target_status=target_status
        )
        assert pre_order == 0
        assert offset == 100

        # reorder_story
        reord_st = f.build_story(status=target_status, order=250)
        next_st = f.build_story(status=target_status, order=300)
        prev_st = f.build_story(status=target_status, order=150)

        # after
        fake_stories_repo.list_story_neighbors.return_value = Neighbor(
            next=next_st, prev=None
        )
        offset, pre_order = await services._calculate_offset(
            total_stories_to_reorder=1,
            target_status=target_status,
            reorder_reference_story=reord_st,
            reorder_place="after",
        )
        assert pre_order == reord_st.order
        assert offset == 25

        fake_stories_repo.list_story_neighbors.return_value = Neighbor(
            next=None, prev=None
        )
        offset, pre_order = await services._calculate_offset(
            total_stories_to_reorder=1,
            target_status=target_status,
            reorder_reference_story=reord_st,
            reorder_place="after",
        )
        assert pre_order == reord_st.order
        assert offset == 100

        # before
        fake_stories_repo.list_story_neighbors.return_value = Neighbor(
            next=None, prev=prev_st
        )
        offset, pre_order = await services._calculate_offset(
            total_stories_to_reorder=1,
            target_status=target_status,
            reorder_reference_story=reord_st,
            reorder_place="before",
        )
        assert pre_order == prev_st.order
        assert offset == 50

        fake_stories_repo.list_story_neighbors.return_value = Neighbor(
            next=None, prev=None
        )
        offset, pre_order = await services._calculate_offset(
            total_stories_to_reorder=1,
            target_status=target_status,
            reorder_reference_story=reord_st,
            reorder_place="before",
        )
        assert pre_order == 0
        assert offset == 125
        reord_st.order = 2
        offset, pre_order = await services._calculate_offset(
            total_stories_to_reorder=1,
            target_status=target_status,
            reorder_reference_story=reord_st,
            reorder_place="before",
        )
        assert pre_order == -198
        assert offset == 100


#######################################################
# update reorder_stories
#######################################################


async def test_reorder_stories_ok():
    user = f.build_user()
    project = f.build_project()
    workflow = f.build_workflow()
    target_status = f.build_workflow_status()
    reorder_story = f.build_story(ref=3)
    s1 = f.build_story(ref=13)
    s2 = f.build_story(ref=54)
    s3 = f.build_story(ref=2)

    with (
        patch(
            "stories.stories.services.workflows_repositories", autospec=True
        ) as fake_workflows_repo,
        patch(
            "stories.stories.services.stories_repositories", autospec=True
        ) as fake_stories_repo,
        patch(
            "stories.stories.services.stories_events", autospec=True
        ) as fake_stories_events,
        patch(
            "stories.stories.services.stories_notifications", autospec=True
        ) as fake_notifications,
    ):
        fake_workflows_repo.get_workflow_status.return_value = target_status
        fake_stories_repo.get_story.return_value = reorder_story
        fake_stories_repo.list_stories_to_reorder.return_value = [s1, s2, s3]

        await services.reorder_stories(
            reordered_by=user,
            project=project,
            target_status_id=target_status.id,
            workflow=workflow,
            stories_refs=[13, 54, 2],
            reorder={"place": "after", "ref": reorder_story.ref},
        )

        fake_stories_repo.bulk_update_stories.assert_awaited_once_with(
            objs_to_update=[s1, s2, s3], fields_to_update=["status", "order"]
        )
        fake_stories_events.emit_when_stories_are_reordered.assert_awaited_once()
        assert fake_notifications.notify_when_story_status_change.await_count == 3


async def test_reorder_story_workflowstatus_does_not_exist():
    user = f.build_user()
    project = f.build_project()
    workflow = f.build_workflow()

    with (
        patch(
            "stories.stories.services.workflows_repositories", autospec=True
        ) as fake_workflows_repo,
        pytest.raises(ex.InvalidStatusError),
    ):
        fake_workflows_repo.get_workflow_status.side_effect = (
            WorkflowStatus.DoesNotExist
        )

        await services.reorder_stories(
            reordered_by=user,
            project=project,
            target_status_id="non-existing",
            workflow=workflow,
            stories_refs=[13, 54, 2],
            reorder={"place": "after", "ref": 3},
        )


async def test_reorder_story_story_ref_does_not_exist():
    user = f.build_user()
    project = f.build_project()
    workflow = f.build_workflow()
    target_status = f.build_workflow_status()

    with (
        patch(
            "stories.stories.services.workflows_repositories", autospec=True
        ) as fake_workflows_repo,
        patch(
            "stories.stories.services.stories_repositories", autospec=True
        ) as fake_stories_repo,
        pytest.raises(ex.InvalidStoryRefError),
    ):
        fake_workflows_repo.get_workflow_status.return_value = target_status

        fake_stories_repo.get_story.return_value = None

        await services.reorder_stories(
            reordered_by=user,
            project=project,
            target_status_id=target_status.id,
            workflow=workflow,
            stories_refs=[13, 54, 2],
            reorder={"place": "after", "ref": 3},
        )


async def test_reorder_story_not_all_stories_exist():
    user = f.build_user()
    project = f.build_project()
    workflow = f.build_workflow()
    target_status = f.build_workflow_status()
    reorder_story = f.build_story(ref=3)

    with (
        patch(
            "stories.stories.services.workflows_repositories", autospec=True
        ) as fake_workflows_repo,
        patch(
            "stories.stories.services.stories_repositories", autospec=True
        ) as fake_stories_repo,
        patch(
            "stories.stories.services.get_latest_story_order", autospec=True
        ) as fake_get_latest_story_order,
        pytest.raises(ex.InvalidStoryRefError),
    ):
        fake_workflows_repo.get_workflow_status.return_value = target_status

        fake_stories_repo.get_story.return_value = reorder_story
        fake_get_latest_story_order.return_value = 0

        await services.reorder_stories(
            reordered_by=user,
            project=project,
            target_status_id=target_status.id,
            workflow=workflow,
            stories_refs=[13, 54, 2],
            reorder={"place": "after", "ref": reorder_story.ref},
        )


#######################################################
# delete story
#######################################################


async def test_delete_story_fail():
    user = f.build_user()
    story = f.build_story()

    with (
        patch(
            "stories.stories.services.stories_repositories", autospec=True
        ) as fake_story_repo,
        patch(
            "stories.stories.services.stories_events", autospec=True
        ) as fake_stories_events,
        patch(
            "stories.stories.services.stories_notifications", autospec=True
        ) as fake_notifications,
    ):
        fake_story_repo.delete_story.return_value = 0

        assert not (await services.delete_story(story=story, deleted_by=user))

        fake_story_repo.delete_story.assert_awaited_once_with(
            story_id=story.id,
        )
        fake_stories_events.emit_event_when_story_is_deleted.assert_not_awaited()
        fake_notifications.notify_when_story_is_deleted.assert_not_awaited()


async def test_delete_story_ok():
    user = f.build_user()
    story = f.build_story()

    with (
        patch(
            "stories.stories.services.stories_repositories", autospec=True
        ) as fake_story_repo,
        patch(
            "stories.stories.services.stories_events", autospec=True
        ) as fake_stories_events,
        patch(
            "stories.stories.services.stories_notifications", autospec=True
        ) as fake_notifications,
    ):
        fake_story_repo.delete_story.return_value = 1

        assert await services.delete_story(story=story, deleted_by=user)
        fake_story_repo.delete_story.assert_awaited_once_with(story_id=story.id)
        fake_stories_events.emit_event_when_story_is_deleted.assert_awaited_once_with(
            project=story.project, ref=story.ref, deleted_by=user
        )
        fake_notifications.notify_when_story_is_deleted.assert_awaited_once_with(
            story=story, emitted_by=user
        )


##########################################################
# reorder_stories
##########################################################


@pytest.mark.django_db
async def test_not_reorder_in_empty_status(project_template) -> None:
    project = await f.create_project(project_template)
    workflow = await sync_to_async(project.workflows.first)()
    status_1 = await sync_to_async(workflow.statuses.first)()
    status_2 = await sync_to_async(workflow.statuses.last)()

    story1 = await f.create_story(project=project, workflow=workflow, status=status_1)
    story2 = await f.create_story(project=project, workflow=workflow, status=status_1)
    story3 = await f.create_story(project=project, workflow=workflow, status=status_1)
    # Current state
    # | status_1 | status_2 |
    # | -------- | -------- |
    # | story1   |          |
    # | story2   |          |
    # | story3   |          |

    await services.reorder_stories(
        reordered_by=project.created_by,
        project=project,
        workflow=workflow,
        target_status_id=status_2.id,
        stories_refs=[story2.ref, story3.ref],
    )
    # Now should be
    # | status_1 | status_2 |
    # | -------- | -------- |
    # | story1   | story2   |
    # |          | story3   |
    stories = [
        story
        async for story in repositories.list_stories_qs(
            filters={"status_id": status_1.id}
        )
    ]
    assert stories[0].ref == story1.ref
    stories = [
        story
        async for story in repositories.list_stories_qs(
            filters={"status_id": status_2.id}
        )
    ]
    assert stories[0].ref == story2.ref
    assert stories[0].order == Decimal(100)
    assert stories[1].ref == story3.ref
    assert stories[1].order == Decimal(200)


@pytest.mark.django_db
async def test_not_reorder_in_populated_status(project_template) -> None:
    project = await f.create_project(project_template)
    workflow = await sync_to_async(project.workflows.first)()
    status_1 = await sync_to_async(workflow.statuses.first)()
    status_2 = await sync_to_async(workflow.statuses.last)()

    story1 = await f.create_story(project=project, workflow=workflow, status=status_1)
    story2 = await f.create_story(project=project, workflow=workflow, status=status_1)
    story3 = await f.create_story(project=project, workflow=workflow, status=status_2)
    # Current state
    # | status_1 | status_2 |
    # | -------- | -------- |
    # | story1   | story3   |
    # | story2   |          |

    await services.reorder_stories(
        reordered_by=project.created_by,
        project=project,
        workflow=workflow,
        target_status_id=status_2.id,
        stories_refs=[story2.ref],
    )
    # Now should be
    # | status_1 | status_2 |
    # | -------- | -------- |
    # | story1   | story3   |
    # |          | story2   |
    stories = [
        story
        async for story in repositories.list_stories_qs(
            filters={"status_id": status_1.id}
        )
    ]
    assert stories[0].ref == story1.ref
    stories = [
        story
        async for story in repositories.list_stories_qs(
            filters={"status_id": status_2.id}
        )
    ]
    assert stories[0].ref == story3.ref
    assert stories[1].ref == story2.ref
    assert stories[1].order == story3.order + 100


@pytest.mark.django_db
async def test_after_in_the_end(project_template) -> None:
    project = await f.create_project(project_template)
    workflow = await sync_to_async(project.workflows.first)()
    status_1 = await sync_to_async(workflow.statuses.first)()
    status_2 = await sync_to_async(workflow.statuses.last)()

    story1 = await f.create_story(project=project, workflow=workflow, status=status_1)
    story2 = await f.create_story(project=project, workflow=workflow, status=status_1)
    story3 = await f.create_story(project=project, workflow=workflow, status=status_2)
    # Current state
    # | status_1 | status_2 |
    # | -------- | -------- |
    # | story1   | story3   |
    # | story2   |          |

    await services.reorder_stories(
        reordered_by=project.created_by,
        project=project,
        workflow=workflow,
        target_status_id=status_2.id,
        stories_refs=[story2.ref],
        reorder={"place": "after", "ref": story3.ref},
    )
    # Now should be
    # | status_1 | status_2 |
    # | -------- | -------- |
    # | story1   | story3   |
    # |          | story2   |
    stories = [
        story
        async for story in repositories.list_stories_qs(
            filters={"status_id": status_1.id}
        )
    ]
    assert stories[0].ref == story1.ref
    stories = [
        story
        async for story in repositories.list_stories_qs(
            filters={"status_id": status_2.id}
        )
    ]
    assert stories[0].ref == story3.ref
    assert stories[1].ref == story2.ref
    assert stories[1].order == story3.order + 100


@pytest.mark.django_db
async def test_after_in_the_middle(project_template) -> None:
    project = await f.create_project(project_template)
    workflow = await sync_to_async(project.workflows.first)()
    status_1 = await sync_to_async(workflow.statuses.first)()
    status_2 = await sync_to_async(workflow.statuses.last)()

    story1 = await f.create_story(project=project, workflow=workflow, status=status_1)
    story2 = await f.create_story(project=project, workflow=workflow, status=status_2)
    story3 = await f.create_story(project=project, workflow=workflow, status=status_2)
    # Current state
    # | status_1 | status_2 |
    # | -------- | -------- |
    # | story1   | story2   |
    # |          | story3   |

    await services.reorder_stories(
        reordered_by=project.created_by,
        project=project,
        workflow=workflow,
        target_status_id=status_2.id,
        stories_refs=[story1.ref],
        reorder={"place": "after", "ref": story2.ref},
    )
    # Now should be
    # | status_1 | status_2 |
    # | -------- | -------- |
    # |          | story2   |
    # |          | story1   |
    # |          | story3   |
    stories = [
        story
        async for story in repositories.list_stories_qs(
            filters={"status_id": status_1.id}
        )
    ]
    assert len(stories) == 0
    stories = [
        story
        async for story in repositories.list_stories_qs(
            filters={"status_id": status_2.id}
        )
    ]
    assert stories[0].ref == story2.ref
    assert stories[1].ref == story1.ref
    assert stories[1].order == story2.order + 100
    assert stories[2].ref == story3.ref
    assert stories[2].order > story3.order


@pytest.mark.django_db
async def test_before_in_the_beginning(project_template) -> None:
    project = await f.create_project(project_template)
    workflow = await sync_to_async(project.workflows.first)()
    status_1 = await sync_to_async(workflow.statuses.first)()
    status_2 = await sync_to_async(workflow.statuses.last)()

    story1 = await f.create_story(project=project, workflow=workflow, status=status_1)
    story2 = await f.create_story(project=project, workflow=workflow, status=status_2)
    story3 = await f.create_story(project=project, workflow=workflow, status=status_2)
    # Current state
    # | status_1 | status_2 |
    # | -------- | -------- |
    # | story1   | story2   |
    # |          | story3   |

    await services.reorder_stories(
        reordered_by=project.created_by,
        project=project,
        workflow=workflow,
        target_status_id=status_2.id,
        stories_refs=[story1.ref],
        reorder={"place": "before", "ref": story2.ref},
    )
    # Now should be
    # | status_1 | status_2 |
    # | -------- | -------- |
    # |          | story1   |
    # |          | story2   |
    # |          | story3   |
    stories = [
        story
        async for story in repositories.list_stories_qs(
            filters={"status_id": status_1.id}
        )
    ]
    assert len(stories) == 0
    stories = [
        story
        async for story in repositories.list_stories_qs(
            filters={"status_id": status_2.id}
        )
    ]
    assert stories[0].ref == story1.ref
    assert stories[0].order == story2.order - 100
    assert stories[1].ref == story2.ref
    assert stories[2].ref == story3.ref


@pytest.mark.django_db
async def test_before_in_the_middle(project_template) -> None:
    project = await f.create_project(project_template)
    workflow = await sync_to_async(project.workflows.first)()
    status_1 = await sync_to_async(workflow.statuses.first)()
    status_2 = await sync_to_async(workflow.statuses.last)()

    story1 = await f.create_story(project=project, workflow=workflow, status=status_1)
    story2 = await f.create_story(project=project, workflow=workflow, status=status_2)
    story3 = await f.create_story(project=project, workflow=workflow, status=status_2)
    # Current state
    # | status_1 | status_2 |
    # | -------- | -------- |
    # | story1   | story2   |
    # |          | story3   |

    await services.reorder_stories(
        reordered_by=project.created_by,
        project=project,
        workflow=workflow,
        target_status_id=status_2.id,
        stories_refs=[story1.ref],
        reorder={"place": "before", "ref": story3.ref},
    )
    # Now should be
    # | status_1 | status_2 |
    # | -------- | -------- |
    # |          | story2   |
    # |          | story1   |
    # |          | story3   |
    stories = [
        story
        async for story in repositories.list_stories_qs(
            filters={"status_id": status_1.id}
        )
    ]
    assert len(stories) == 0
    stories = [
        story
        async for story in repositories.list_stories_qs(
            filters={"status_id": status_2.id}
        )
    ]
    assert stories[0].ref == story2.ref
    assert stories[1].ref == story1.ref
    assert stories[1].order == story2.order + 100
    assert stories[2].ref == story3.ref
    assert stories[2].order > story3.order


@pytest.mark.django_db
async def test_before_in_the_middle_far_away(project_template) -> None:
    project = await f.create_project(project_template)
    workflow = await sync_to_async(project.workflows.first)()
    status_1 = await sync_to_async(workflow.statuses.first)()
    status_2 = await sync_to_async(workflow.statuses.last)()

    story1 = await f.create_story(project=project, workflow=workflow, status=status_1)
    story2 = await f.create_story(project=project, workflow=workflow, status=status_2)
    story3 = await f.create_story(
        project=project, workflow=workflow, status=status_2, order=story2.order + 100
    )
    # Current state
    # | status_1 | status_2 |
    # | -------- | -------- |
    # | story1   | story2   |
    # |          | story3   |

    await services.reorder_stories(
        reordered_by=project.created_by,
        project=project,
        workflow=workflow,
        target_status_id=status_2.id,
        stories_refs=[story1.ref],
        reorder={"place": "before", "ref": story3.ref},
    )
    # Now should be
    # | status_1 | status_2 |
    # | -------- | -------- |
    # |          | story2   |
    # |          | story1   |
    # |          | story3   |
    stories = [
        story
        async for story in repositories.list_stories_qs(
            filters={"status_id": status_1.id}
        )
    ]
    assert len(stories) == 0
    stories = [
        story
        async for story in repositories.list_stories_qs(
            filters={"status_id": status_2.id}
        )
    ]
    assert stories[0].ref == story2.ref
    assert stories[1].ref == story1.ref
    assert stories[1].order == story2.order + ((story3.order - story2.order) // 2)
    assert stories[2].ref == story3.ref
    assert stories[2].order == story3.order


@pytest.mark.django_db
async def test_before_in_the_middle_multiple(project_template) -> None:
    project = await f.create_project(project_template)
    workflow = await sync_to_async(project.workflows.first)()
    status_1 = await sync_to_async(workflow.statuses.first)()
    status_2 = await sync_to_async(workflow.statuses.last)()

    story1 = await f.create_story(project=project, workflow=workflow, status=status_1)
    story2 = await f.create_story(project=project, workflow=workflow, status=status_2)
    story3 = await f.create_story(project=project, workflow=workflow, status=status_2)
    story4 = await f.create_story(project=project, workflow=workflow, status=status_2)
    story5 = await f.create_story(
        project=project, workflow=workflow, status=status_2, order=story4.order + 100
    )
    # Current state
    # | status_1 | status_2 |
    # | -------- | -------- |
    # | story1   | story2   |
    # |          | story3   |
    # |          | story4   |
    # |          | story5   |

    await services.reorder_stories(
        reordered_by=project.created_by,
        project=project,
        workflow=workflow,
        target_status_id=status_2.id,
        stories_refs=[story1.ref],
        reorder={"place": "before", "ref": story3.ref},
    )
    # Now should be
    # | status_1 | status_2 |
    # | -------- | -------- |
    # |          | story2   |
    # |          | story1   |
    # |          | story3   |
    # |          | story4   |
    # |          | story5   |
    stories = [
        story
        async for story in repositories.list_stories_qs(
            filters={"status_id": status_1.id}
        )
    ]
    assert len(stories) == 0
    stories = [
        story
        async for story in repositories.list_stories_qs(
            filters={"status_id": status_2.id}
        )
    ]
    assert stories[0].ref == story2.ref
    assert stories[1].ref == story1.ref
    assert stories[1].order == story2.order + ((story5.order - story2.order) // 4)
    assert stories[2].ref == story3.ref
    assert stories[2].order > story3.order
    assert stories[3].ref == story4.ref
    assert stories[3].order > story4.order
    assert stories[4].ref == story5.ref
    assert stories[4].order == story5.order


@pytest.mark.django_db
async def test_after_in_the_middle_multiple_same_status(project_template) -> None:
    project = await f.create_project(project_template)
    workflow = await sync_to_async(project.workflows.first)()
    status_1 = await sync_to_async(workflow.statuses.first)()

    story1 = await f.create_story(project=project, workflow=workflow, status=status_1)
    story2 = await f.create_story(project=project, workflow=workflow, status=status_1)
    story3 = await f.create_story(project=project, workflow=workflow, status=status_1)
    story4 = await f.create_story(project=project, workflow=workflow, status=status_1)
    story5 = await f.create_story(
        project=project, workflow=workflow, status=status_1, order=story4.order + 100
    )
    # Current state
    # | status_1 |
    # | -------- |
    # | story1   |
    # | story2   |
    # | story3   |
    # | story4   |
    # | story5   |

    await services.reorder_stories(
        reordered_by=project.created_by,
        project=project,
        workflow=workflow,
        target_status_id=status_1.id,
        stories_refs=[story2.ref, story3.ref, story5.ref],
        reorder={"place": "after", "ref": story1.ref},
    )
    # Now should be
    # | status_1 |
    # | -------- |
    # | story1   |
    # | story2   |
    # | story3   |
    # | story5   |
    # | story4   |
    stories = [
        story
        async for story in repositories.list_stories_qs(
            filters={"status_id": status_1.id}
        )
    ]
    assert stories[0].ref == story1.ref
    assert stories[1].ref == story2.ref
    assert stories[1].order == story1.order + 100 * 1
    assert stories[2].ref == story3.ref
    assert stories[2].order == story1.order + 100 * 2
    assert stories[3].ref == story5.ref
    assert stories[3].order == story1.order + 100 * 3
    assert stories[4].ref == story4.ref
    # Not enough space, story4 was moved also
    assert stories[4].order == story1.order + 100 * 4


##########################################################
# misc - get_latest_story_order
##########################################################


@pytest.mark.django_db
async def test_get_latest_story_order(project_template):
    project = await f.create_project(project_template)
    workflow = await sync_to_async(project.workflows.first)()
    status_1 = await sync_to_async(workflow.statuses.first)()
    status_2 = await sync_to_async(workflow.statuses.last)()

    assert await services.get_latest_story_order(status_1.id) is None

    story1 = await f.create_story(project=project, workflow=workflow, status=status_1)
    assert await services.get_latest_story_order(status_1.id) == story1.order
    story2 = await f.create_story(project=project, workflow=workflow, status=status_2)
    assert await services.get_latest_story_order(status_2.id) == story2.order
    story3 = await f.create_story(project=project, workflow=workflow, status=status_2)

    assert await services.get_latest_story_order(status_1.id) == story1.order
    assert await services.get_latest_story_order(status_2.id) == story3.order


#######################################################
# utils
#######################################################


def build_workflow_serializer(story):
    return WorkflowSerializer(
        id=story.workflow.id,
        project_id=story.workflow.project_id,
        name=story.workflow.name,
        slug=story.workflow.slug,
        order=story.workflow.order,
        statuses=[build_nested_status_serializer(story.status)],
    )


def build_nested_status_serializer(status):
    return WorkflowStatusNestedSerializer(
        id=status.id,
        name=status.name,
        color=status.color,
        order=status.order,
    )
