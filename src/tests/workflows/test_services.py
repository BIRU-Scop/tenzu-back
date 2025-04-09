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
from unittest.mock import call, patch

import pytest
from django.test import override_settings

from base.repositories.neighbors import Neighbor
from tests.utils import factories as f
from workflows import repositories, services
from workflows.serializers import (
    DeleteWorkflowSerializer,
    ReorderWorkflowStatusesSerializer,
    WorkflowNestedSerializer,
    WorkflowSerializer,
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
        patch("django.db.transaction.atomic", autospec=True),
    ):
        fake_workflows_repo.list_workflows.return_value = None
        fake_workflows_repo.create_workflow.return_value = workflow
        fake_workflows_repo.list_workflow_statuses.return_value = []

        workflow = await services.create_workflow(
            project=workflow.project, name=workflow.name
        )

        fake_workflows_repo.list_workflows.assert_awaited_once_with(
            filters={"project_id": project.id}, order_by=["-order"]
        )
        fake_workflows_repo.create_workflow.assert_awaited_once_with(
            project=project, name=workflow.name, order=100
        )
        fake_projects_repo.get_project_template.assert_awaited_once()
        fake_workflows_repo.apply_default_workflow_statuses.assert_awaited_once()
        fake_workflows_repo.list_workflow_statuses.assert_awaited_once()

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
        patch("django.db.transaction.atomic", autospec=True),
    ):
        fake_workflows_repo.list_workflows.return_value = [workflow2]
        fake_workflows_repo.create_workflow.return_value = workflow1
        fake_workflows_repo.list_workflow_statuses.return_value = []

        workflow = await services.create_workflow(
            project=workflow1.project, name=workflow1.name
        )

        fake_workflows_repo.list_workflows.assert_awaited_once_with(
            filters={"project_id": project.id}, order_by=["-order"]
        )
        fake_workflows_repo.create_workflow.assert_awaited_once()
        fake_projects_repo.get_project_template.assert_awaited_once()
        fake_workflows_repo.apply_default_workflow_statuses.assert_awaited_once()
        fake_workflows_repo.list_workflow_statuses.assert_awaited_once()

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
        patch("django.db.transaction.atomic", autospec=True),
        override_settings(**{"MAX_NUM_WORKFLOWS": 1}),
        pytest.raises(ex.MaxNumWorkflowCreatedError),
    ):
        fake_workflows_repo.list_workflows.return_value = [workflow1]

        await services.create_workflow(project=workflow2.project, name=workflow2.name)

        fake_workflows_repo.list_workflows.assert_awaited_once_with(
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
        fake_workflows_repo.list_workflows.return_value = workflows
        fake_workflows_repo.list_workflow_statuses.return_value = [workflow_status]
        await services.list_workflows(project_id=workflows[0].project.id)
        fake_workflows_repo.list_workflows.assert_awaited_once_with(
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
        await services.get_workflow(
            project_id=workflow.project.id, workflow_slug=workflow.slug
        )
        fake_workflows_repo.get_workflow.assert_awaited_once()


async def test_get_detailed_workflow_ok():
    workflow_status = f.build_workflow_status()
    workflow = f.build_workflow(statuses=[workflow_status])

    with (
        patch(
            "workflows.services.workflows_repositories", autospec=True
        ) as fake_workflows_repo,
        patch(
            "workflows.services.serializers_services", autospec=True
        ) as fake_workflows_serializers,
    ):
        fake_workflows_repo.get_workflow.return_value = workflow
        fake_workflows_repo.list_workflow_statuses.return_value = [workflow_status]
        fake_workflows_serializers.serialize_workflow.return_value = WorkflowSerializer(
            id=workflow.id,
            project_id=workflow.project_id,
            name=workflow.name,
            slug=workflow.slug,
            order=workflow.order,
            statuses=[workflow_status],
        )
        await services.get_workflow_detail(
            project_id=workflow.project_id, workflow_slug=workflow.slug
        )
        fake_workflows_repo.get_workflow.assert_awaited_once()
        fake_workflows_serializers.serialize_workflow.assert_called_once()


async def test_get_delete_workflow_detail_ok():
    with (
        patch(
            "workflows.services.workflows_repositories", autospec=True
        ) as fake_workflows_repo,
        patch(
            "workflows.services.serializers_services", autospec=True
        ) as fake_workflows_serializers,
        patch(
            "workflows.services.stories_services", autospec=True
        ) as fake_stories_services,
    ):
        workflow_status = f.build_workflow_status()
        workflow = f.build_workflow(statuses=[workflow_status])
        fake_workflows_serializers.serialize_delete_workflow_detail.return_value = (
            DeleteWorkflowSerializer(
                id=workflow.id,
                name=workflow.name,
                slug=workflow.slug,
                order=workflow.order,
                statuses=[workflow_status],
                stories=[],
            )
        )
        fake_stories_services.list_stories.return_value = []
        workflow_statuses = [workflow_status]
        fake_workflows_repo.get_workflow.return_value = workflow
        fake_workflows_repo.list_workflow_statuses.return_value = workflow_statuses
        await services.get_delete_workflow_detail(
            project_id=workflow.project_id, workflow_slug=workflow.slug
        )
        fake_workflows_repo.get_workflow.assert_awaited_once()
        fake_workflows_repo.list_workflow_statuses.assert_awaited_once_with(
            workflow_id=workflow.id
        )
        fake_stories_services.list_stories.assert_awaited_once_with(
            project_id=workflow.project_id,
            workflow_slug=workflow.slug,
            get_assignees=False,
        )
        fake_workflows_serializers.serialize_delete_workflow_detail.assert_called_once()


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
        patch("workflows.services.get_workflow_detail", autospec=True),
        patch(
            "workflows.services.workflows_events", autospec=True
        ) as fake_workflows_events,
        patch(
            "workflows.services.projects_services", autospec=True
        ) as fake_projects_services,
        patch("django.db.transaction.atomic", autospec=True),
    ):
        updated_workflow = await services.update_workflow(
            project_id=project.id, workflow=workflow, updated_by=user, values=values
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
        patch("workflows.services.get_workflow_detail", autospec=True),
        patch("workflows.services.workflows_events", autospec=True),
        patch(
            "workflows.services.projects_services", autospec=True
        ) as fake_projects_services,
        patch("django.db.transaction.atomic", autospec=True),
    ):
        await services.update_workflow(
            project_id=workflow.project.id,
            workflow=workflow,
            updated_by=user,
            values=values,
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
        fake_workflows_repo.list_workflow_statuses.return_value = None
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
            order=Decimal(100),
            workflow=status.workflow,
        )

        fake_workflows_repo.list_workflow_statuses.assert_awaited_once_with(
            workflow_id=workflow.id, order_by=["-order"], offset=0, limit=1
        )

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
            "workflows.services.get_delete_workflow_detail", autospec=True
        ) as fake_get_delete_workflow_detail,
        patch(
            "workflows.services.projects_services", autospec=True
        ) as fake_projects_services,
        patch("django.db.transaction.atomic", autospec=True),
    ):
        user = f.build_user()
        workflow = f.build_workflow()
        status1 = f.build_workflow_status(workflow=workflow, order=1)
        status2 = f.build_workflow_status(workflow=workflow, order=2)
        status3 = f.build_workflow_status(workflow=workflow, order=3)
        fake_get_delete_workflow_detail.return_value = DeleteWorkflowSerializer(
            id=workflow.id,
            name=workflow.name,
            slug=workflow.slug,
            order=workflow.order,
            statuses=[status1, status2, status3],
            stories=[],
        )
        fake_workflows_repo.get_workflow.return_value = workflow
        fake_workflows_repo.list_workflow_statuses.return_value = [
            status1,
            status2,
            status3,
        ]
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
            "workflows.services.get_delete_workflow_detail", autospec=True
        ) as fake_get_delete_workflow_detail,
        patch(
            "workflows.services.projects_repositories", autospec=True
        ) as fake_projects_repo,
        patch(
            "workflows.services.projects_services", autospec=True
        ) as fake_projects_services,
        patch("django.db.transaction.atomic", autospec=True),
    ):
        user = f.build_user()
        workflow = f.build_workflow(
            slug="landing-w", project__landing_page="k/landing-w"
        )
        status1 = f.build_workflow_status(workflow=workflow, order=1)
        fake_get_delete_workflow_detail.return_value = DeleteWorkflowSerializer(
            id=workflow.id,
            name=workflow.name,
            slug=workflow.slug,
            order=workflow.order,
            statuses=[status1],
            stories=[],
        )
        fake_workflows_repo.get_workflow.return_value = workflow
        fake_workflows_repo.list_workflow_statuses.return_value = [
            status1,
        ]
        fake_workflows_repo.delete_workflow.return_value = True
        fake_projects_repo.get_first_workflow_slug.return_value = None

        ret = await services.delete_workflow(workflow=workflow, deleted_by=user)

        fake_projects_services.update_project_landing_page.assert_awaited_once_with(
            project=workflow.project
        )

        fake_workflows_events.emit_event_when_workflow_is_deleted.assert_awaited_once()
        assert ret is True


async def test_delete_workflow_with_target_workflow_with_anchor_status_ok():
    with (
        patch(
            "workflows.services.workflows_repositories", autospec=True
        ) as fake_workflows_repo,
        patch(
            "workflows.services.get_workflow_detail", autospec=True
        ) as fake_get_workflow_detail,
        patch(
            "workflows.services.get_delete_workflow_detail", autospec=True
        ) as fake_get_delete_workflow_detail,
        patch("workflows.services.get_workflow", autospec=True) as fake_get_workflow,
        patch(
            "workflows.services.reorder_workflow_statuses", autospec=True
        ) as fake_reorder_workflow_statuses,
        patch(
            "workflows.services.workflows_events", autospec=True
        ) as fake_workflows_events,
        patch("django.db.transaction.atomic", autospec=True),
    ):
        user = f.build_user()
        deleted_workflow = f.build_workflow(slug="deleted_workflow")
        deleted_workflow_status1 = f.build_workflow_status(
            workflow=deleted_workflow, order=1
        )
        deleted_workflow_status2 = f.build_workflow_status(
            workflow=deleted_workflow, order=2
        )
        deleted_workflow_statuses = [deleted_workflow_status1, deleted_workflow_status2]
        deleted_workflow_detail = DeleteWorkflowSerializer(
            id=deleted_workflow.id,
            name=deleted_workflow.name,
            slug=deleted_workflow.slug,
            order=deleted_workflow.order,
            statuses=deleted_workflow_statuses,
            stories=[],
        )
        fake_get_delete_workflow_detail.return_value = deleted_workflow_detail
        target_workflow = f.build_workflow(slug="target_workflow")
        target_workflow_status1 = f.build_workflow_status(
            workflow=target_workflow, order=1
        )
        target_workflow_status2 = f.build_workflow_status(
            workflow=target_workflow, order=2
        )
        target_workflow_statuses = [target_workflow_status2, target_workflow_status1]
        target_workflow_detail = WorkflowSerializer(
            id=target_workflow.id,
            project_id=target_workflow.project_id,
            name=target_workflow.name,
            slug=target_workflow.slug,
            order=target_workflow.order,
            statuses=target_workflow_statuses,
        )

        fake_get_workflow.return_value = target_workflow
        fake_get_workflow_detail.return_value = target_workflow_detail
        # the serializer response doesn't maters
        fake_reorder_workflow_statuses.return_value = ReorderWorkflowStatusesSerializer(
            workflow=WorkflowNestedSerializer(
                id=target_workflow.id,
                project_id=target_workflow.project_id,
                name=deleted_workflow.name,
                slug=deleted_workflow.slug,
            ),
            statuses=[],
            reorder=None,
        )
        fake_workflows_repo.list_workflow_statuses.side_effect = [
            deleted_workflow_statuses,
            target_workflow_statuses,
        ]
        fake_workflows_repo.delete_workflow.return_value = True
        # service call
        ret = await services.delete_workflow(
            workflow=deleted_workflow,
            deleted_by=user,
            target_workflow_slug=target_workflow.slug,
        )
        # asserts
        fake_workflows_repo.list_workflow_statuses.assert_has_awaits(
            [
                call(
                    workflow_id=deleted_workflow.id,
                    is_empty=False,
                    order_by=["order"],
                ),
                call(
                    workflow_id=target_workflow.id,
                    order_by=["-order"],
                    offset=0,
                    limit=1,
                ),
            ]
        )
        fake_workflows_repo.delete_workflow.assert_awaited_once_with(
            filters={"id": deleted_workflow.id}
        )
        fake_reorder_workflow_statuses.assert_awaited_once_with(
            target_workflow=target_workflow,
            statuses=[status.id for status in deleted_workflow_statuses],
            reorder={"place": "after", "status": target_workflow_statuses[0].id},
            source_workflow=deleted_workflow,
        )
        fake_get_workflow_detail.assert_awaited_once_with(
            project_id=target_workflow.project.id, workflow_slug=target_workflow.slug
        )
        fake_get_delete_workflow_detail.assert_awaited_once_with(
            project_id=deleted_workflow.project.id, workflow_slug=deleted_workflow.slug
        )
        fake_workflows_events.emit_event_when_workflow_is_deleted.assert_awaited_once_with(
            project=deleted_workflow.project,
            workflow=deleted_workflow_detail,
            target_workflow=target_workflow_detail,
        )
        assert ret is True


async def test_delete_workflow_with_target_workflow_with_no_anchor_status_ok():
    with (
        patch(
            "workflows.services.workflows_repositories", autospec=True
        ) as fake_workflows_repo,
        patch(
            "workflows.services.get_workflow_detail", autospec=True
        ) as fake_get_workflow_detail,
        patch(
            "workflows.services.get_delete_workflow_detail", autospec=True
        ) as fake_get_delete_workflow_detail,
        patch("workflows.services.get_workflow", autospec=True) as fake_get_workflow,
        patch(
            "workflows.services.reorder_workflow_statuses", autospec=True
        ) as fake_reorder_workflow_statuses,
        patch(
            "workflows.services.workflows_events", autospec=True
        ) as fake_workflows_events,
        patch("django.db.transaction.atomic", autospec=True),
    ):
        user = f.build_user()
        deleted_workflow = f.build_workflow(slug="deleted_workflow")
        deleted_workflow_status1 = f.build_workflow_status(
            workflow=deleted_workflow, order=1
        )
        deleted_workflow_statuses = [deleted_workflow_status1]
        deleted_workflow_detail = DeleteWorkflowSerializer(
            id=deleted_workflow.id,
            name=deleted_workflow.name,
            slug=deleted_workflow.slug,
            order=deleted_workflow.order,
            statuses=deleted_workflow_statuses,
            stories=[],
        )
        fake_get_delete_workflow_detail.return_value = deleted_workflow_detail
        target_workflow = f.build_workflow(slug="target_workflow")
        target_workflow_statuses = []
        target_workflow_detail = WorkflowSerializer(
            id=target_workflow.id,
            project_id=target_workflow.project_id,
            name=target_workflow.name,
            slug=target_workflow.slug,
            order=target_workflow.order,
            statuses=target_workflow_statuses,
        )

        fake_get_workflow.return_value = target_workflow
        fake_get_workflow_detail.return_value = target_workflow_detail
        # the serializer response doesn't maters
        fake_reorder_workflow_statuses.return_value = ReorderWorkflowStatusesSerializer(
            workflow=WorkflowNestedSerializer(
                id=target_workflow.id,
                project_id=target_workflow.project_id,
                name=deleted_workflow.name,
                slug=deleted_workflow.slug,
            ),
            statuses=[],
            reorder=None,
        )
        fake_workflows_repo.list_workflow_statuses.side_effect = [
            deleted_workflow_statuses,
            target_workflow_statuses,
        ]
        fake_workflows_repo.delete_workflow.return_value = True
        # service call
        ret = await services.delete_workflow(
            workflow=deleted_workflow,
            deleted_by=user,
            target_workflow_slug=target_workflow.slug,
        )
        # asserts
        fake_workflows_repo.list_workflow_statuses.assert_has_awaits(
            [
                call(
                    workflow_id=deleted_workflow.id,
                    is_empty=False,
                    order_by=["order"],
                ),
                call(
                    workflow_id=target_workflow.id,
                    order_by=["-order"],
                    offset=0,
                    limit=1,
                ),
            ]
        )
        fake_workflows_repo.delete_workflow.assert_awaited_once_with(
            filters={"id": deleted_workflow.id}
        )
        fake_reorder_workflow_statuses.assert_awaited_once_with(
            target_workflow=target_workflow,
            statuses=[status.id for status in deleted_workflow_statuses],
            reorder=None,
            source_workflow=deleted_workflow,
        )
        fake_get_workflow_detail.assert_awaited_once_with(
            project_id=target_workflow.project.id, workflow_slug=target_workflow.slug
        )
        fake_workflows_events.emit_event_when_workflow_is_deleted.assert_awaited_once_with(
            project=deleted_workflow.project,
            workflow=deleted_workflow_detail,
            target_workflow=target_workflow_detail,
        )
        assert ret is True


async def test_delete_workflow_not_existing_target_workflow_exception():
    with (
        patch(
            "workflows.services.workflows_repositories", autospec=True
        ) as fake_workflows_repo,
        patch(
            "workflows.services.get_delete_workflow_detail", autospec=True
        ) as fake_get_delete_workflow_detail,
        patch("workflows.services.get_workflow", autospec=True) as fake_get_workflow,
        patch(
            "workflows.services.reorder_workflow_statuses", autospec=True
        ) as fake_reorder_workflow_statuses,
        patch(
            "workflows.services.workflows_events", autospec=True
        ) as fake_workflows_events,
        patch("django.db.transaction.atomic", autospec=True),
        pytest.raises(ex.NonExistingMoveToWorkflow),
    ):
        user = f.build_user()
        deleted_workflow = f.build_workflow(slug="deleted_workflow")
        deleted_workflow_detail = DeleteWorkflowSerializer(
            id=deleted_workflow.id,
            name=deleted_workflow.name,
            slug=deleted_workflow.slug,
            order=deleted_workflow.order,
            statuses=[],
            stories=[],
        )
        target_workflow = f.build_workflow(slug="target_workflow")
        fake_get_delete_workflow_detail.return_value = deleted_workflow_detail
        fake_get_workflow.return_value = None

        # service call
        ret = await services.delete_workflow(
            workflow=deleted_workflow,
            deleted_by=user,
            target_workflow_slug=target_workflow.slug,
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
            "workflows.services.get_delete_workflow_detail", autospec=True
        ) as fake_get_delete_workflow_detail,
        patch("workflows.services.get_workflow", autospec=True) as fake_get_workflow,
        patch(
            "workflows.services.reorder_workflow_statuses", autospec=True
        ) as fake_reorder_workflow_statuses,
        patch(
            "workflows.services.workflows_events", autospec=True
        ) as fake_workflows_events,
        patch("django.db.transaction.atomic", autospec=True),
        pytest.raises(ex.SameMoveToWorkflow),
    ):
        user = f.build_user()
        deleted_workflow = f.build_workflow(slug="deleted_workflow")
        deleted_workflow_detail = DeleteWorkflowSerializer(
            id=deleted_workflow.id,
            name=deleted_workflow.name,
            slug=deleted_workflow.slug,
            order=deleted_workflow.order,
            statuses=[],
            stories=[],
        )
        fake_get_delete_workflow_detail.return_value = deleted_workflow_detail
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
            statuses=[status3.id, status2.id],
            reorder={"place": "after", "status": status1.id},
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
            statuses=[status3.id, status2.id],
            reorder={"place": "after", "status": status1.id},
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
            statuses=[status1.id, status2.id],
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
            statuses=[status1.id, status2.id],
            reorder=None,
            source_workflow=workflow,
        )


async def test_reorder_workflow_status_repeated():
    with (
        pytest.raises(ex.InvalidWorkflowStatusError),
        patch(
            "workflows.services.workflows_repositories", autospec=True
        ) as fake_workflows_repo,
    ):
        workflow = f.build_workflow()
        status = f.build_workflow_status(workflow=workflow, order=1)
        fake_workflows_repo.list_workflow_statuses_to_reorder.return_value = [status]

        await services.reorder_workflow_statuses(
            target_workflow=workflow,
            statuses=[status.id],
            reorder={"place": "after", "status": status.id},
        )


async def test_reorder_anchor_workflow_status_does_not_exist():
    with (
        patch(
            "workflows.services.workflows_repositories", autospec=True
        ) as fake_workflows_repo,
        pytest.raises(ex.InvalidWorkflowStatusError),
    ):
        fake_workflows_repo.get_workflow_status.return_value = None

        await services.reorder_workflow_statuses(
            target_workflow=f.build_workflow(),
            statuses=["in-progress"],
            reorder={"place": "after", "status": "mooo"},
        )


async def test_reorder_any_workflow_status_does_not_exist():
    with (
        patch(
            "workflows.services.workflows_repositories", autospec=True
        ) as fake_workflows_repo,
        pytest.raises(ex.InvalidWorkflowStatusError),
    ):
        fake_workflows_repo.get_workflow_status.return_value = None

        await services.reorder_workflow_statuses(
            target_workflow=f.build_workflow(),
            statuses=["in-progress", "mooo"],
            reorder={"place": "after", "status": "new"},
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
        statuses=[status2.id, status3.id, status5.id],
        reorder={"place": "after", "status": status1.id},
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
    ):
        fake_workflows_repo.delete_workflow_status.return_value = 1
        fake_get_workflow_status.return_value = workflow_status2
        fake_stories_repo.list_stories.return_value.values_list.return_value.__aiter__.return_value = workflow_status1_stories_ref
        fake_stories_services.reorder_stories.return_value = None

        await services.delete_workflow_status(
            workflow_status=workflow_status1,
            target_status_id=workflow_status2.id,
            deleted_by=user,
        )

        fake_get_workflow_status.assert_awaited_once_with(
            project_id=workflow.project.id,
            workflow_slug=workflow.slug,
            id=workflow_status2.id,
        )
        fake_stories_repo.list_stories.assert_called_once_with(
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
    ):
        fake_workflows_repo.delete_workflow_status.return_value = 2
        fake_workflows_repo.get_workflow_status.return_value = 1
        fake_stories_repo.list_stories.return_value.values_list.return_value.__aiter__.return_value = workflow_status1_stories_ref
        fake_stories_services.reorder_stories.return_value = None

        await services.delete_workflow_status(
            workflow_status=workflow_status1, target_status_id=None, deleted_by=user
        )

        fake_get_workflow_status.assert_not_awaited()
        fake_stories_repo.list_stories.assert_not_called()
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
        pytest.raises(ex.NonExistingMoveToStatus),
    ):
        fake_get_workflow_status.return_value = None

        await services.delete_workflow_status(
            workflow_status=workflow_status1,
            target_status_id=workflow_status2.id,
            deleted_by=user,
        )

        fake_get_workflow_status.assert_awaited_once_with(
            project_id=workflow.project.id,
            workflow_slug=workflow.slug,
            id=workflow_status2.id,
        )


async def test_delete_workflow_status_same_target_status_ex():
    user = f.create_user()
    workflow = f.build_workflow()
    workflow_status1 = f.build_workflow_status(workflow=workflow)

    with (
        patch(
            "workflows.services.get_workflow_status", autospec=True
        ) as fake_get_workflow_status,
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
            id=workflow_status1.id,
        )
