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

from unittest.mock import patch

import pytest
from django.test import override_settings

from base.repositories.neighbors import Neighbor
from tests.utils import factories as f
from tests.utils.bad_params import NOT_EXISTING_SLUG
from tests.utils.utils import patch_db_transaction
from workflows import repositories, services
from workflows.models import Workflow, WorkflowStatus
from workflows.serializers import (
    DeleteWorkflowSerializer,
    ReorderWorkflowStatusesSerializer,
    WorkflowNestedSerializer,
)
from workflows.services import exceptions as ex

#######################################################
# create_workflow
#######################################################


async def test_create_workflow_ok():
    project = f.build_project()
    workflow = f.build_workflow(project=project)

    with (
        patch(
            "workflows.services.workflows_repositories", autospec=True
        ) as fake_workflows_repo,
        patch(
            "workflows.services.projects_repositories", autospec=True
        ) as fake_projects_repo,
        patch(
            "workflows.services.workflows_events", autospec=True
        ) as fake_workflows_events,
        patch_db_transaction(),
    ):
        fake_workflows_repo.list_workflows_qs.return_value.values_list.return_value.__aiter__.return_value = []
        fake_workflows_repo.create_workflow.return_value = workflow
        fake_workflows_repo.apply_default_workflow_statuses.return_value = []

        workflow = await services.create_workflow(
            project=workflow.project, name=workflow.name
        )

        fake_workflows_repo.list_workflows_qs.assert_called_once_with(
            filters={"project_id": project.id}, order_by=["-order"]
        )
        fake_workflows_repo.create_workflow.assert_awaited_once_with(
            project=project, name=workflow.name, order=100
        )
        fake_projects_repo.get_project_template.assert_awaited_once()
        fake_workflows_repo.apply_default_workflow_statuses.assert_awaited_once()

        fake_projects_repo.update_project.assert_awaited_once_with(
            project,
            values={"landing_page": f"kanban/{workflow.slug}"},
        )

        fake_workflows_events.emit_event_when_workflow_is_created.assert_awaited_once_with(
            project=project, workflow=workflow
        )


async def test_create_workflow_no_landing_change():
    project = f.build_project()
    workflow1 = f.build_workflow(project=project)
    workflow2 = f.build_workflow(project=project)

    with (
        patch(
            "workflows.services.workflows_repositories", autospec=True
        ) as fake_workflows_repo,
        patch(
            "workflows.services.projects_repositories", autospec=True
        ) as fake_projects_repo,
        patch(
            "workflows.services.workflows_events", autospec=True
        ) as fake_workflows_events,
        patch_db_transaction(),
    ):
        fake_workflows_repo.list_workflows_qs.return_value.values_list.return_value.__aiter__.return_value = [
            workflow2.order
        ]
        fake_workflows_repo.create_workflow.return_value = workflow1
        fake_workflows_repo.apply_default_workflow_statuses.return_value = []

        workflow = await services.create_workflow(
            project=workflow1.project, name=workflow1.name
        )

        fake_workflows_repo.list_workflows_qs.assert_called_once_with(
            filters={"project_id": project.id}, order_by=["-order"]
        )
        fake_workflows_repo.create_workflow.assert_awaited_once()
        fake_projects_repo.get_project_template.assert_awaited_once()
        fake_workflows_repo.apply_default_workflow_statuses.assert_awaited_once()
        fake_workflows_repo.list_workflow_statuses.assert_not_awaited()

        fake_projects_repo.update_project.assert_not_awaited()

        fake_workflows_events.emit_event_when_workflow_is_created.assert_awaited_once_with(
            project=project, workflow=workflow
        )


async def test_create_workflow_reached_num_workflows_error():
    project = f.build_project()
    workflow1 = f.build_workflow(project=project)
    workflow2 = f.build_workflow(project=project)

    with (
        patch(
            "workflows.services.workflows_repositories", autospec=True
        ) as fake_workflows_repo,
        patch(
            "workflows.services.projects_repositories", autospec=True
        ) as fake_projects_repo,
        patch(
            "workflows.services.workflows_events", autospec=True
        ) as fake_workflows_events,
        patch_db_transaction(),
        override_settings(**{"MAX_NUM_WORKFLOWS": 1}),
        pytest.raises(ex.MaxNumWorkflowCreatedError),
    ):
        fake_workflows_repo.list_workflows_qs.return_value.values_list.return_value.__aiter__.return_value = [
            workflow1.order
        ]
        await services.create_workflow(project=workflow2.project, name=workflow2.name)

        fake_workflows_repo.list_workflows_qs.assert_called_once_with(
            filters={"project_id": project.id}, order_by=["-order"]
        )
        fake_workflows_repo.create_workflow.assert_not_awaited()
        fake_projects_repo.get_project_template.assert_not_awaited()
        fake_workflows_repo.apply_default_workflow_statuses.assert_not_awaited()
        fake_workflows_repo.list_workflow_statuses.assert_not_awaited()
        fake_workflows_events.emit_event_when_workflow_is_created.assert_not_awaited()


#######################################################
# list_workflows
#######################################################


async def test_list_workflows_ok():
    workflow_status = f.build_workflow_status()
    workflows = [f.build_workflow(statuses=[workflow_status])]

    with patch(
        "workflows.services.workflows_repositories", autospec=True
    ) as fake_workflows_repo:
        fake_workflows_repo.list_workflows_qs.return_value.__aiter__.return_value = (
            workflows
        )
        fake_workflows_repo.list_workflow_statuses.return_value = [workflow_status]
        await services.list_workflows(project_id=workflows[0].project.id)
        fake_workflows_repo.list_workflows_qs.assert_called_once_with(
            filters={"project_id": workflows[0].project.id},
            prefetch_related=["statuses"],
        )


#######################################################
# get_workflow
#######################################################


async def test_get_workflow_ok():
    workflow = f.build_workflow()

    with patch(
        "workflows.services.workflows_repositories", autospec=True
    ) as fake_workflows_repo:
        fake_workflows_repo.get_workflow.return_value = workflow
        await services.get_workflow_by_slug(
            project_id=workflow.project.id, workflow_slug=workflow.slug
        )
        fake_workflows_repo.get_workflow.assert_awaited_once()


#######################################################
# update_workflow
#######################################################


async def test_update_workflow_ok():
    user = f.build_user()
    project = f.build_project()
    workflow = f.build_workflow(project=project)
    values = {"name": "updated name"}

    with (
        patch(
            "workflows.services.workflows_repositories", autospec=True
        ) as fake_workflows_repo,
        patch(
            "workflows.services.workflows_events", autospec=True
        ) as fake_workflows_events,
        patch(
            "workflows.services.projects_services", autospec=True
        ) as fake_projects_services,
        patch_db_transaction(),
    ):
        updated_workflow = await services.update_workflow(
            workflow=workflow, updated_by=user, values=values
        )
        fake_workflows_repo.update_workflow.assert_awaited_once_with(
            workflow=workflow, values=values
        )
        fake_workflows_events.emit_event_when_workflow_is_updated.assert_awaited_once_with(
            project=project,
            workflow=updated_workflow,
        )
        fake_projects_services.update_project_landing_page.assert_not_called()


async def test_update_workflow_update_landing_to_new_slug():
    user = f.build_user()
    workflow = f.build_workflow(slug="landing-w", project__landing_page="k/landing-w")
    values = {"name": "updated name"}

    with (
        patch("workflows.services.workflows_repositories", autospec=True),
        patch("workflows.services.workflows_events", autospec=True),
        patch(
            "workflows.services.projects_services", autospec=True
        ) as fake_projects_services,
        patch_db_transaction(),
    ):
        await services.update_workflow(
            workflow=workflow, updated_by=user, values=values
        )
        fake_projects_services.update_project_landing_page.assert_awaited_once()


#######################################################
# create_workflow_status
#######################################################


async def test_create_workflow_status_ok():
    workflow = f.build_workflow()
    status = f.build_workflow_status(workflow=workflow)

    with (
        patch(
            "workflows.services.workflows_repositories", autospec=True
        ) as fake_workflows_repo,
        patch(
            "workflows.services.workflows_events", autospec=True
        ) as fake_workflows_events,
    ):
        fake_workflows_repo.create_workflow_status.return_value = status
        fake_workflows_repo.get_workflow_statusreturn_value = status

        workflow_status = await services.create_workflow_status(
            name=status.name,
            color=status.color,
            workflow=status.workflow,
        )

        fake_workflows_repo.create_workflow_status.assert_awaited_once_with(
            name=status.name,
            color=status.color,
            workflow=status.workflow,
        )

        fake_workflows_repo.list_workflow_statuses.assert_not_awaited()

        fake_workflows_events.emit_event_when_workflow_status_is_created.assert_awaited_once_with(
            project=workflow.project, workflow_status=workflow_status
        )


#######################################################
# update_workflow_status
#######################################################


async def test_update_workflow_status_ok():
    workflow = f.build_workflow()
    status = f.build_workflow_status(workflow=workflow)
    values = {"name": "New status name"}

    with (
        patch(
            "workflows.services.workflows_repositories", autospec=True
        ) as fake_workflows_repo,
        patch(
            "workflows.services.workflows_events", autospec=True
        ) as fake_workflows_events,
    ):
        fake_workflows_repo.update_workflow_status.return_value = status
        await services.update_workflow_status(workflow_status=status, values=values)
        fake_workflows_repo.update_workflow_status.assert_awaited_once_with(
            workflow_status=status, values=values
        )
        fake_workflows_events.emit_event_when_workflow_status_is_updated.assert_awaited_once_with(
            project=workflow.project, workflow_status=status
        )


async def test_update_workflow_status_noop():
    status = f.build_workflow_status()
    values = {}

    with (
        patch(
            "workflows.services.workflows_repositories", autospec=True
        ) as fake_workflows_repo,
        patch(
            "workflows.services.workflows_events", autospec=True
        ) as fake_workflows_events,
    ):
        ret_status = await services.update_workflow_status(
            workflow_status=status, values=values
        )

        assert ret_status == status
        fake_workflows_repo.update_workflow_status.assert_not_awaited()
        fake_workflows_events.emit_event_when_workflow_status_is_updated.assert_not_awaited()


async def test_update_workflow_status_none_name():
    status = f.build_workflow_status()
    values = {"name": None}

    with (
        pytest.raises(ex.TenzuServiceException),
        patch(
            "workflows.services.workflows_repositories", autospec=True
        ) as fake_workflows_repo,
        patch(
            "workflows.services.workflows_events", autospec=True
        ) as fake_workflows_events,
    ):
        await services.update_workflow_status(workflow_status=status, values=values)
        fake_workflows_repo.update_workflow_status.assert_not_awaited()
        fake_workflows_events.emit_event_when_workflow_status_is_updated.assert_not_awaited()


#######################################################
# delete workflow
#######################################################


async def test_delete_workflow_no_target_workflow_ok():
    with (
        patch(
            "workflows.services.workflows_repositories", autospec=True
        ) as fake_workflows_repo,
        patch(
            "workflows.services.workflows_events", autospec=True
        ) as fake_workflows_events,
        patch(
            "workflows.services.projects_services", autospec=True
        ) as fake_projects_services,
        patch(
            "workflows.services.stories_services", autospec=True
        ) as fake_stories_services,
        patch_db_transaction(),
    ):
        user = f.build_user()
        status1 = f.build_workflow_status(order=1)
        status2 = f.build_workflow_status(order=2)
        status3 = f.build_workflow_status(order=3)
        workflow = f.build_workflow(statuses=[status1, status2, status3])
        fake_workflows_repo.get_workflow.return_value = workflow
        fake_workflows_repo.list_workflow_statuses.return_value = [
            status1,
            status2,
            status3,
        ]
        fake_stories_services.list_stories.return_value = []
        fake_workflows_repo.delete_workflow.return_value = True

        ret = await services.delete_workflow(workflow=workflow, deleted_by=user)

        fake_workflows_repo.delete_workflow.assert_awaited_once_with(
            filters={"id": workflow.id}
        )
        fake_workflows_events.emit_event_when_workflow_is_deleted.assert_awaited_once()
        assert ret is True
        fake_projects_services.update_project_landing_page.assert_not_called()


async def test_delete_workflow_update_landing_to_new_slug():
    with (
        patch(
            "workflows.services.workflows_repositories", autospec=True
        ) as fake_workflows_repo,
        patch(
            "workflows.services.workflows_events", autospec=True
        ) as fake_workflows_events,
        patch(
            "workflows.services.projects_repositories", autospec=True
        ) as fake_projects_repo,
        patch(
            "workflows.services.projects_services", autospec=True
        ) as fake_projects_services,
        patch(
            "workflows.services.stories_services", autospec=True
        ) as fake_stories_services,
        patch_db_transaction(),
    ):
        user = f.build_user()
        status1 = f.build_workflow_status(order=1)
        workflow = f.build_workflow(
            slug="landing-w", project__landing_page="k/landing-w", statuses=[status1]
        )
        fake_workflows_repo.get_workflow.return_value = workflow
        fake_workflows_repo.delete_workflow.return_value = True
        fake_projects_repo.get_first_workflow_slug.return_value = None

        ret = await services.delete_workflow(workflow=workflow, deleted_by=user)

        fake_projects_services.update_project_landing_page.assert_awaited_once_with(
            project=workflow.project, updated_by=user
        )

        fake_workflows_events.emit_event_when_workflow_is_deleted.assert_awaited_once()
        assert ret is True


async def test_delete_workflow_with_target_workflow_with_anchor_status_ok():
    with (
        patch(
            "workflows.services.workflows_repositories", autospec=True
        ) as fake_workflows_repo,
        patch(
            "workflows.services.get_workflow_by_slug", autospec=True
        ) as fake_get_workflow,
        patch(
            "workflows.services.reorder_workflow_statuses", autospec=True
        ) as fake_reorder_workflow_statuses,
        patch(
            "workflows.services.workflows_events", autospec=True
        ) as fake_workflows_events,
        patch(
            "workflows.services.stories_services", autospec=True
        ) as fake_stories_services,
        patch_db_transaction(),
    ):
        user = f.build_user()
        deleted_workflow_status1 = f.build_workflow_status(order=1)
        deleted_workflow_status2 = f.build_workflow_status(order=2)
        deleted_workflow_statuses = [deleted_workflow_status1, deleted_workflow_status2]
        deleted_workflow = f.build_workflow(
            slug="deleted_workflow", statuses=deleted_workflow_statuses
        )
        target_workflow_status1 = f.build_workflow_status(order=1)
        target_workflow_status2 = f.build_workflow_status(order=2)
        target_workflow_statuses = [target_workflow_status1, target_workflow_status2]
        target_workflow = f.build_workflow(
            slug="target_workflow", statuses=target_workflow_statuses
        )

        fake_get_workflow.return_value = target_workflow
        # the serializer response doesn't maters
        fake_reorder_workflow_statuses.return_value = ReorderWorkflowStatusesSerializer(
            workflow=WorkflowNestedSerializer(
                id=target_workflow.id,
                project_id=target_workflow.project_id,
                name=deleted_workflow.name,
                slug=deleted_workflow.slug,
            ),
            status_ids=[],
            reorder=None,
        )
        fake_workflows_repo.list_workflow_statuses.return_value = (
            deleted_workflow_statuses
        )
        fake_workflows_repo.delete_workflow.return_value = True
        # service call
        ret = await services.delete_workflow(
            workflow=deleted_workflow,
            deleted_by=user,
            target_workflow_slug=target_workflow.slug,
        )
        # asserts
        fake_workflows_repo.list_workflow_statuses.assert_awaited_once_with(
            workflow_id=deleted_workflow.id,
            is_empty=False,
            order_by=["order"],
        )
        fake_workflows_repo.delete_workflow.assert_awaited_once_with(
            filters={"id": deleted_workflow.id}
        )
        fake_reorder_workflow_statuses.assert_awaited_once_with(
            target_workflow=target_workflow,
            status_ids=[status.id for status in deleted_workflow_statuses],
            reorder={"place": "after", "status_id": target_workflow_status2.id},
            source_workflow=deleted_workflow,
        )
        fake_workflows_events.emit_event_when_workflow_is_deleted.assert_awaited_once_with(
            project=deleted_workflow.project,
            workflow=DeleteWorkflowSerializer(
                id=deleted_workflow.id,
                name=deleted_workflow.name,
                slug=deleted_workflow.slug,
                order=deleted_workflow.order,
                statuses=deleted_workflow_statuses,
                stories=[],
            ),
            target_workflow=target_workflow,
        )
        assert ret is True


async def test_delete_workflow_with_target_workflow_with_no_anchor_status_ok():
    with (
        patch(
            "workflows.services.workflows_repositories", autospec=True
        ) as fake_workflows_repo,
        patch(
            "workflows.services.get_workflow_by_slug", autospec=True
        ) as fake_get_workflow,
        patch(
            "workflows.services.reorder_workflow_statuses", autospec=True
        ) as fake_reorder_workflow_statuses,
        patch(
            "workflows.services.workflows_events", autospec=True
        ) as fake_workflows_events,
        patch(
            "workflows.services.stories_services", autospec=True
        ) as fake_stories_services,
        patch_db_transaction(),
    ):
        user = f.build_user()
        deleted_workflow_status1 = f.build_workflow_status(order=1)
        deleted_workflow_statuses = [deleted_workflow_status1]
        deleted_workflow = f.build_workflow(
            slug="deleted_workflow", statuses=deleted_workflow_statuses
        )
        target_workflow = f.build_workflow(slug="target_workflow", statuses=[])

        fake_get_workflow.return_value = target_workflow
        # the serializer response doesn't matters
        fake_reorder_workflow_statuses.return_value = ReorderWorkflowStatusesSerializer(
            workflow=WorkflowNestedSerializer(
                id=target_workflow.id,
                project_id=target_workflow.project_id,
                name=deleted_workflow.name,
                slug=deleted_workflow.slug,
            ),
            status_ids=[],
            reorder=None,
        )
        fake_workflows_repo.list_workflow_statuses.return_value = (
            deleted_workflow_statuses
        )
        fake_workflows_repo.delete_workflow.return_value = True
        # service call
        ret = await services.delete_workflow(
            workflow=deleted_workflow,
            deleted_by=user,
            target_workflow_slug=target_workflow.slug,
        )
        # asserts
        fake_workflows_repo.list_workflow_statuses.assert_awaited_once_with(
            workflow_id=deleted_workflow.id,
            is_empty=False,
            order_by=["order"],
        )
        fake_workflows_repo.delete_workflow.assert_awaited_once_with(
            filters={"id": deleted_workflow.id}
        )
        fake_reorder_workflow_statuses.assert_awaited_once_with(
            target_workflow=target_workflow,
            status_ids=[status.id for status in deleted_workflow_statuses],
            reorder=None,
            source_workflow=deleted_workflow,
        )
        fake_workflows_events.emit_event_when_workflow_is_deleted.assert_awaited_once_with(
            project=deleted_workflow.project,
            workflow=DeleteWorkflowSerializer(
                id=deleted_workflow.id,
                name=deleted_workflow.name,
                slug=deleted_workflow.slug,
                order=deleted_workflow.order,
                statuses=deleted_workflow_statuses,
            ),
            target_workflow=target_workflow,
        )
        assert ret is True


async def test_delete_workflow_not_existing_target_workflow_exception():
    with (
        patch(
            "workflows.services.workflows_repositories", autospec=True
        ) as fake_workflows_repo,
        patch(
            "workflows.services.get_workflow_by_slug", autospec=True
        ) as fake_get_workflow,
        patch(
            "workflows.services.reorder_workflow_statuses", autospec=True
        ) as fake_reorder_workflow_statuses,
        patch(
            "workflows.services.workflows_events", autospec=True
        ) as fake_workflows_events,
        patch_db_transaction(),
        pytest.raises(ex.NonExistingMoveToWorkflow),
    ):
        user = f.build_user()
        deleted_workflow = f.build_workflow(slug="deleted_workflow")
        fake_get_workflow.side_effect = Workflow.DoesNotExist

        # service call
        ret = await services.delete_workflow(
            workflow=deleted_workflow,
            deleted_by=user,
            target_workflow_slug=NOT_EXISTING_SLUG,
        )

        # asserts
        fake_reorder_workflow_statuses.assert_not_awaited()
        fake_workflows_repo.delete_workflow.assert_not_awaited()
        fake_workflows_events.emit_event_when_workflow_is_deleted.assert_not_awaited()

        assert ret is False


async def test_delete_workflow_same_target_workflow_exception():
    with (
        patch(
            "workflows.services.workflows_repositories", autospec=True
        ) as fake_workflows_repo,
        patch(
            "workflows.services.get_workflow_by_slug", autospec=True
        ) as fake_get_workflow,
        patch(
            "workflows.services.reorder_workflow_statuses", autospec=True
        ) as fake_reorder_workflow_statuses,
        patch(
            "workflows.services.workflows_events", autospec=True
        ) as fake_workflows_events,
        patch_db_transaction(),
        pytest.raises(ex.SameMoveToWorkflow),
    ):
        user = f.build_user()
        deleted_workflow = f.build_workflow(slug="deleted_workflow", statuses=[])
        fake_get_workflow.return_value = deleted_workflow

        # service call
        ret = await services.delete_workflow(
            workflow=deleted_workflow,
            deleted_by=user,
            target_workflow_slug=deleted_workflow.slug,
        )

        # asserts
        fake_reorder_workflow_statuses.assert_not_awaited()
        fake_workflows_repo.delete_workflow.assert_not_awaited()
        fake_workflows_events.emit_event_when_workflow_is_deleted.assert_not_awaited()

        assert ret is True


#######################################################
# _calculate_offset
#######################################################


async def test_calculate_offset() -> None:
    workflow = f.build_workflow()

    with (
        patch(
            "workflows.services.workflows_repositories", autospec=True
        ) as fake_workflows_repo,
    ):
        prev_st = f.build_workflow_status(workflow=workflow, order=150)
        reord_st = f.build_workflow_status(workflow=workflow, order=250)
        next_st = f.build_workflow_status(workflow=workflow, order=300)

        # after
        fake_workflows_repo.list_workflow_status_neighbors.return_value = Neighbor(
            prev=None, next=next_st
        )
        offset, pre_order = await services._calculate_offset(
            total_statuses_to_reorder=1,
            workflow=workflow,
            reorder_reference_status=reord_st,
            reorder_place="after",
        )
        assert pre_order == reord_st.order
        assert offset == 25

        fake_workflows_repo.list_workflow_status_neighbors.return_value = Neighbor(
            next=None, prev=None
        )
        offset, pre_order = await services._calculate_offset(
            total_statuses_to_reorder=1,
            workflow=workflow,
            reorder_reference_status=reord_st,
            reorder_place="after",
        )
        assert pre_order == reord_st.order
        assert offset == 100

        # before
        fake_workflows_repo.list_workflow_status_neighbors.return_value = Neighbor(
            next=None, prev=prev_st
        )
        offset, pre_order = await services._calculate_offset(
            total_statuses_to_reorder=1,
            workflow=workflow,
            reorder_reference_status=reord_st,
            reorder_place="before",
        )
        assert pre_order == prev_st.order
        assert offset == 50

        fake_workflows_repo.list_workflow_status_neighbors.return_value = Neighbor(
            next=None, prev=None
        )
        offset, pre_order = await services._calculate_offset(
            total_statuses_to_reorder=1,
            workflow=workflow,
            reorder_reference_status=reord_st,
            reorder_place="before",
        )
        assert pre_order == 0
        assert offset == 125


#######################################################
# update reorder_statuses
#######################################################


async def test_reorder_workflow_statuses_same_workflow_ok():
    with (
        patch(
            "workflows.services.workflows_repositories", autospec=True
        ) as fake_workflows_repo,
        patch(
            "workflows.services.stories_repositories", autospec=True
        ) as fake_stories_repo,
        patch(
            "workflows.services.workflows_events", autospec=True
        ) as fake_workflows_events,
        patch_db_transaction(),
    ):
        workflow = f.build_workflow()
        status1 = f.build_workflow_status(workflow=workflow, order=1)
        status2 = f.build_workflow_status(workflow=workflow, order=2)
        status3 = f.build_workflow_status(workflow=workflow, order=3)
        fake_workflows_repo.get_workflow_status.return_value = status1
        fake_workflows_repo.list_workflow_statuses_to_reorder.return_value = [
            status3,
            status2,
        ]
        fake_workflows_repo.list_workflow_status_neighbors.return_value = Neighbor(
            prev=None, next=None
        )

        await services.reorder_workflow_statuses(
            target_workflow=f.build_workflow(),
            status_ids=[status3.id, status2.id],
            reorder={"place": "after", "status_id": status1.id},
        )

        fake_stories_repo.bulk_update_workflow_to_stories.assert_not_awaited()
        fake_workflows_repo.bulk_update_workflow_statuses.assert_awaited_once_with(
            objs_to_update=[status3, status2], fields_to_update=["order", "workflow"]
        )
        fake_workflows_events.emit_event_when_workflow_statuses_are_reordered.assert_awaited_once()
        assert status1.order == 1
        assert status2.order == 201
        assert status3.order == 101


async def test_reorder_workflow_statuses_between_workflows_with_anchor_ok():
    with (
        patch(
            "workflows.services.workflows_repositories", autospec=True
        ) as fake_workflows_repo,
        patch(
            "workflows.services.stories_repositories", autospec=True
        ) as fake_stories_repo,
        patch(
            "workflows.services.workflows_events", autospec=True
        ) as fake_workflows_events,
        patch_db_transaction(),
    ):
        workflow1 = f.build_workflow()
        workflow2 = f.build_workflow()
        status1 = f.build_workflow_status(workflow=workflow1, order=1)
        status2 = f.build_workflow_status(workflow=workflow1, order=2)
        status3 = f.build_workflow_status(workflow=workflow1, order=3)
        fake_workflows_repo.get_workflow_status.return_value = status1
        fake_workflows_repo.list_workflow_statuses_to_reorder.return_value = [
            status3,
            status2,
        ]
        fake_stories_repo.bulk_update_workflow_to_stories.return_value = None

        await services.reorder_workflow_statuses(
            target_workflow=workflow1,
            status_ids=[status3.id, status2.id],
            reorder={"place": "after", "status_id": status1.id},
            source_workflow=workflow2,
        )

        fake_workflows_repo.bulk_update_workflow_statuses.assert_awaited_once_with(
            objs_to_update=[status3, status2], fields_to_update=["order", "workflow"]
        )
        fake_stories_repo.bulk_update_workflow_to_stories.assert_awaited_once_with(
            statuses_ids=[status3.id, status2.id],
            old_workflow_id=workflow2.id,
            new_workflow_id=workflow1.id,
        )
        fake_workflows_events.emit_event_when_workflow_statuses_are_reordered.assert_awaited_once()


async def test_reorder_workflow_statuses_between_workflows_no_anchor_ok():
    with (
        patch(
            "workflows.services.workflows_repositories", autospec=True
        ) as fake_workflows_repo,
        patch(
            "workflows.services.stories_repositories", autospec=True
        ) as fake_stories_repo,
        patch(
            "workflows.services.workflows_events", autospec=True
        ) as fake_workflows_events,
        patch_db_transaction(),
    ):
        workflow1 = f.build_workflow()
        workflow2 = f.build_workflow(statuses=[])
        status1 = f.build_workflow_status(workflow=workflow1, order=1)
        status2 = f.build_workflow_status(workflow=workflow1, order=2)
        fake_workflows_repo.get_workflow_status.return_value = status1
        fake_workflows_repo.list_workflow_statuses_to_reorder.return_value = [
            status1,
            status2,
        ]
        fake_stories_repo.bulk_update_workflow_to_stories.return_value = None

        await services.reorder_workflow_statuses(
            target_workflow=workflow2,
            status_ids=[status1.id, status2.id],
            reorder=None,
            source_workflow=workflow1,
        )

        fake_workflows_repo.bulk_update_workflow_statuses.assert_awaited_once_with(
            objs_to_update=[status1, status2], fields_to_update=["order", "workflow"]
        )
        fake_stories_repo.bulk_update_workflow_to_stories.assert_awaited_once_with(
            statuses_ids=[status1.id, status2.id],
            old_workflow_id=workflow1.id,
            new_workflow_id=workflow2.id,
        )
        fake_workflows_events.emit_event_when_workflow_statuses_are_reordered.assert_awaited_once()


async def test_reorder_workflow_statuses_between_workflows_no_anchor_same_workflow_exception():
    with (
        patch(
            "workflows.services.workflows_repositories", autospec=True
        ) as fake_workflows_repo,
        patch_db_transaction(),
        pytest.raises(ex.NonExistingMoveToStatus),
    ):
        workflow = f.build_workflow()
        status1 = f.build_workflow_status(workflow=workflow, order=1)
        status2 = f.build_workflow_status(workflow=workflow, order=2)
        fake_workflows_repo.list_workflow_statuses_to_reorder.return_value = [
            status1,
            status2,
        ]

        await services.reorder_workflow_statuses(
            target_workflow=workflow,
            status_ids=[status1.id, status2.id],
            reorder=None,
            source_workflow=workflow,
        )


async def test_reorder_workflow_status_repeated():
    with (
        patch(
            "workflows.services.workflows_repositories", autospec=True
        ) as fake_workflows_repo,
        patch_db_transaction(),
        pytest.raises(ex.InvalidWorkflowStatusError),
    ):
        workflow = f.build_workflow()
        status = f.build_workflow_status(workflow=workflow, order=1)
        fake_workflows_repo.list_workflow_statuses_to_reorder.return_value = [status]

        await services.reorder_workflow_statuses(
            target_workflow=workflow,
            status_ids=[status.id],
            reorder={"place": "after", "status_id": status.id},
        )


async def test_reorder_anchor_workflow_status_does_not_exist():
    with (
        patch(
            "workflows.services.workflows_repositories", autospec=True
        ) as fake_workflows_repo,
        patch_db_transaction(),
        pytest.raises(ex.InvalidWorkflowStatusError),
    ):
        fake_workflows_repo.get_workflow_status.return_value = None

        await services.reorder_workflow_statuses(
            target_workflow=f.build_workflow(),
            status_ids=["in-progress"],
            reorder={"place": "after", "status_id": "mooo"},
        )


async def test_reorder_any_workflow_status_does_not_exist():
    with (
        patch(
            "workflows.services.workflows_repositories", autospec=True
        ) as fake_workflows_repo,
        patch_db_transaction(),
        pytest.raises(ex.InvalidWorkflowStatusError),
    ):
        fake_workflows_repo.get_workflow_status.return_value = None

        await services.reorder_workflow_statuses(
            target_workflow=f.build_workflow(),
            status_ids=["in-progress", "mooo"],
            reorder={"place": "after", "status_id": "new"},
        )


@pytest.mark.django_db
async def test_after_in_the_middle_multiple() -> None:
    workflow = await f.create_workflow(statuses=[])
    status1 = await f.create_workflow_status(workflow=workflow, order=1)
    status2 = await f.create_workflow_status(workflow=workflow, order=2)
    status3 = await f.create_workflow_status(workflow=workflow, order=3)
    status4 = await f.create_workflow_status(workflow=workflow, order=4)
    status5 = await f.create_workflow_status(workflow=workflow, order=5)

    await services.reorder_workflow_statuses(
        target_workflow=workflow,
        status_ids=[status2.id, status3.id, status5.id],
        reorder={"place": "after", "status_id": status1.id},
        source_workflow=workflow,
    )

    statuses = await repositories.list_workflow_statuses(workflow_id=workflow.id)
    assert statuses[0].id == status1.id
    assert statuses[1].id == status2.id
    assert statuses[1].order == status1.order + 100 * 1
    assert statuses[2].id == status3.id
    assert statuses[2].order == status1.order + 100 * 2
    assert statuses[3].id == status5.id
    assert statuses[3].order == status1.order + 100 * 3
    assert statuses[4].id == status4.id
    # Not enough space, status4 was moved also
    assert statuses[4].order == status1.order + 100 * 4


#######################################################
# delete_workflow_status
#######################################################


async def test_delete_workflow_status_moving_stories_ok():
    user = f.create_user()
    workflow = f.build_workflow()
    workflow_status1 = f.build_workflow_status(workflow=workflow)
    workflow_status2 = f.build_workflow_status(workflow=workflow)
    workflow_status1_stories_ref = [
        f.build_story(status=workflow_status1, workflow=workflow).ref
    ]

    with (
        patch(
            "workflows.services.workflows_repositories", autospec=True
        ) as fake_workflows_repo,
        patch(
            "workflows.services.stories_repositories", autospec=True
        ) as fake_stories_repo,
        patch(
            "workflows.services.workflows_events", autospec=True
        ) as fake_workflows_events,
        patch(
            "workflows.services.get_workflow_status", autospec=True
        ) as fake_get_workflow_status,
        patch(
            "workflows.services.stories_services", autospec=True
        ) as fake_stories_services,
        patch_db_transaction(),
    ):
        fake_workflows_repo.delete_workflow_status.return_value = 1
        fake_get_workflow_status.return_value = workflow_status2
        fake_stories_repo.list_stories_qs.return_value.values_list.return_value.__aiter__.return_value = workflow_status1_stories_ref
        fake_stories_services.reorder_stories.return_value = None

        await services.delete_workflow_status(
            workflow_status=workflow_status1,
            target_status_id=workflow_status2.id,
            deleted_by=user,
        )

        fake_get_workflow_status.assert_awaited_once_with(
            status_id=workflow_status2.id,
        )
        fake_stories_repo.list_stories_qs.assert_called_once_with(
            filters={
                "status_id": workflow_status1.id,
            },
            order_by=["order"],
        )
        fake_stories_services.reorder_stories.assert_awaited_once_with(
            reordered_by=user,
            project=workflow_status1.project,
            workflow=workflow,
            target_status_id=workflow_status2.id,
            stories_refs=workflow_status1_stories_ref,
        )
        fake_workflows_repo.delete_workflow_status.assert_awaited_once_with(
            status_id=workflow_status1.id
        )
        fake_workflows_events.emit_event_when_workflow_status_is_deleted.assert_awaited_once_with(
            project=workflow_status1.project,
            workflow_status=workflow_status1,
            target_status=workflow_status2,
        )


async def test_delete_workflow_status_deleting_stories_ok():
    user = f.create_user()
    workflow = f.build_workflow()
    workflow_status1 = f.build_workflow_status(workflow=workflow)
    workflow_status1_stories_ref = [
        f.build_story(status=workflow_status1, workflow=workflow).ref
    ]

    with (
        patch(
            "workflows.services.workflows_repositories", autospec=True
        ) as fake_workflows_repo,
        patch(
            "workflows.services.stories_repositories", autospec=True
        ) as fake_stories_repo,
        patch(
            "workflows.services.workflows_events", autospec=True
        ) as fake_workflows_events,
        patch(
            "workflows.services.get_workflow_status", autospec=True
        ) as fake_get_workflow_status,
        patch(
            "workflows.services.stories_services", autospec=True
        ) as fake_stories_services,
        patch_db_transaction(),
    ):
        fake_workflows_repo.delete_workflow_status.return_value = 2
        fake_workflows_repo.get_workflow_status.return_value = 1
        fake_stories_repo.list_stories_qs.return_value.values_list.return_value.__aiter__.return_value = workflow_status1_stories_ref
        fake_stories_services.reorder_stories.return_value = None

        await services.delete_workflow_status(
            workflow_status=workflow_status1, target_status_id=None, deleted_by=user
        )

        fake_get_workflow_status.assert_not_awaited()
        fake_stories_repo.list_stories_qs.assert_not_called()
        fake_stories_services.reorder_stories.assert_not_awaited()
        fake_workflows_repo.delete_workflow_status.assert_awaited_once_with(
            status_id=workflow_status1.id
        )
        fake_workflows_events.emit_event_when_workflow_status_is_deleted.assert_awaited_once_with(
            project=workflow_status1.project,
            workflow_status=workflow_status1,
            target_status=None,
        )


async def test_delete_workflow_status_wrong_target_status_ex():
    user = f.create_user()
    workflow = f.build_workflow()
    workflow_status1 = f.build_workflow_status(workflow=workflow)
    workflow_status2 = f.build_workflow_status(workflow=workflow)

    with (
        patch(
            "workflows.services.get_workflow_status", autospec=True
        ) as fake_get_workflow_status,
        patch_db_transaction(),
        pytest.raises(ex.NonExistingMoveToStatus),
    ):
        fake_get_workflow_status.side_effect = WorkflowStatus.DoesNotExist

        await services.delete_workflow_status(
            workflow_status=workflow_status1,
            target_status_id=workflow_status2.id,
            deleted_by=user,
        )

        fake_get_workflow_status.assert_awaited_once_with(
            workflow_id=workflow.id,
            status_id=workflow_status2.id,
        )


async def test_delete_workflow_status_same_target_status_ex():
    user = f.create_user()
    workflow = f.build_workflow()
    workflow_status1 = f.build_workflow_status(workflow=workflow)

    with (
        patch(
            "workflows.services.get_workflow_status", autospec=True
        ) as fake_get_workflow_status,
        patch_db_transaction(),
        pytest.raises(ex.SameMoveToStatus),
    ):
        fake_get_workflow_status.return_value = workflow_status1

        await services.delete_workflow_status(
            workflow_status=workflow_status1,
            target_status_id=workflow_status1.id,
            deleted_by=user,
        )

        fake_get_workflow_status.assert_awaited_once_with(
            project_id=workflow.project.id,
            workflow_slug=workflow.slug,
            status_id=workflow_status1.id,
        )
