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

from unittest import IsolatedAsyncioTestCase

import pytest
from asgiref.sync import sync_to_async

from commons.ordering import DEFAULT_ORDER_OFFSET
from projects.projects.models import Project
from tests.utils import factories as f
from tests.utils.bad_params import NOT_EXISTING_UUID
from workflows import repositories
from workflows.models import Workflow, WorkflowStatus

pytestmark = pytest.mark.django_db


##########################################################
# create_workflow
##########################################################


async def test_create_workflow(project_template):
    project = await f.create_project(project_template)
    workflow_res = await repositories.create_workflow(
        name="workflow",
        order=1,
        project=project,
    )
    assert workflow_res.name == "workflow"
    assert workflow_res.project == project


##########################################################
# list_workflows
##########################################################


async def test_list_workflows_schemas_ok(project_template) -> None:
    project = await f.create_project(project_template)
    workflows = [
        w
        async for w in repositories.list_workflows_qs(
            filters={"project_id": project.id}, prefetch_related=["statuses"]
        )
    ]

    assert len(workflows) == 1
    assert len(await _list_workflow_statuses(workflow=workflows[0])) == 4
    assert hasattr(workflows[0], "id")


async def test_list_project_without_workflows_ok() -> None:
    project = await f.create_simple_project()
    workflows = [
        w
        async for w in repositories.list_workflows_qs(
            filters={"project_id": project.id}
        )
    ]

    assert len(workflows) == 0


##########################################################
# get_workflow
##########################################################


async def test_get_workflow_ok(project_template) -> None:
    project = await f.create_project(project_template)
    workflows = await _list_workflows(project=project)
    workflow = await repositories.get_workflow(
        filters={"project_id": project.id, "slug": workflows[0].slug}
    )
    assert workflow is not None
    assert hasattr(workflow, "id")


async def test_get_project_without_workflow_ok() -> None:
    project = await f.create_simple_project()
    with pytest.raises(Workflow.DoesNotExist):
        await repositories.get_workflow(
            filters={"project_id": project.id, "slug": "not-existing-slug"}
        )


##########################################################
# update_workflow
##########################################################


async def test_update_workflow():
    workflow = await f.create_workflow()
    updated_workflow = await repositories.update_workflow(
        workflow=workflow,
        values={"name": "Updated name"},
    )
    assert updated_workflow.name == "Updated name"


#########################################################
# delete workflow
##########################################################


async def test_delete_workflow_without_workflow_statuses_ok(project_template) -> None:
    project = await f.create_project(project_template)
    workflow = await f.create_workflow(project=project, statuses=[])

    delete_ret = await repositories.delete_workflow(filters={"id": workflow.id})
    assert delete_ret == 1


async def test_delete_workflow_with_workflow_statuses_ok(project_template) -> None:
    project = await f.create_project(project_template)
    workflow = await f.create_workflow(project=project)

    delete_ret = await repositories.delete_workflow(filters={"id": workflow.id})
    assert delete_ret == 1


##########################################################
# create_workflow_status
##########################################################


async def test_create_workflow_status():
    workflow = await f.create_workflow()

    workflow_status_res = await repositories.create_workflow_status(
        name="workflow-status1",
        color=1,
        workflow=workflow,
    )
    assert workflow_status_res.name == "workflow-status1"
    assert workflow_status_res.workflow_id == workflow.id
    assert workflow_status_res.order == DEFAULT_ORDER_OFFSET

    workflow_status_res = await repositories.create_workflow_status(
        name="workflow-status2",
        color=2,
        workflow=workflow,
    )
    assert workflow_status_res.name == "workflow-status2"
    assert workflow_status_res.workflow_id == workflow.id
    assert workflow_status_res.order == DEFAULT_ORDER_OFFSET * 2


##########################################################
# list_workflows_statuses
##########################################################


class ListWorkflowStatuses(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.empty_workflow = await f.create_workflow(statuses=[])
        self.workflow = await f.create_workflow(statuses=[])
        self.workflow_status = await f.create_workflow_status(workflow=self.workflow)
        await f.create_story(status=self.workflow_status, workflow=self.workflow)
        self.empty_workflow_status = await f.create_workflow_status(
            workflow=self.workflow
        )

    async def test_list_workflows_statuses_ok(self) -> None:
        statuses = await repositories.list_workflow_statuses(
            workflow_id=self.workflow.id
        )
        assert len(statuses) > 0

    async def test_list_no_workflows_statuses(self) -> None:
        statuses = await repositories.list_workflow_statuses(
            workflow_id=self.empty_workflow.id
        )
        assert len(statuses) == 0

    async def test_list_empty_statuses(self) -> None:
        statuses = await repositories.list_workflow_statuses(
            workflow_id=self.workflow.id, is_empty=True
        )
        assert self.empty_workflow_status in statuses
        assert self.workflow_status not in statuses
        assert len(statuses) == 1

    async def test_list_not_empty_statuses(self) -> None:
        statuses = await repositories.list_workflow_statuses(
            workflow_id=self.workflow.id, is_empty=False
        )
        assert self.workflow_status in statuses
        assert self.empty_workflow_status not in statuses
        assert len(statuses) == 1


##########################################################
# list_workflows_statuses_to_reorder
##########################################################


async def test_list_statuses_to_reorder(project_template) -> None:
    project = await f.create_project(project_template)
    workflow = await sync_to_async(project.workflows.first)()
    st_ids = [s.id for s in await _list_workflow_statuses(workflow=workflow)]

    # New(0), Ready(1), In progress(2), Done(3)

    statuses = [st_ids[1], st_ids[0], st_ids[3]]
    statuses = await repositories.list_workflow_statuses_to_reorder(
        workflow_id=workflow.id, ids=statuses
    )
    assert statuses[0].id == statuses[0].id
    assert statuses[1].id == statuses[1].id
    assert statuses[2].id == statuses[2].id

    statuses = [st_ids[3], st_ids[1], st_ids[0]]
    statuses = await repositories.list_workflow_statuses_to_reorder(
        workflow_id=workflow.id, ids=statuses
    )
    assert statuses[0].id == statuses[0].id
    assert statuses[1].id == statuses[1].id
    assert statuses[2].id == statuses[2].id

    statuses = [st_ids[0], st_ids[1]]
    statuses = await repositories.list_workflow_statuses_to_reorder(
        workflow_id=workflow.id, ids=statuses
    )
    assert statuses[0].id == statuses[0].id
    assert statuses[1].id == statuses[1].id


async def test_list_statuses_to_reorder_bad_ids(project_template) -> None:
    project = await f.create_project(project_template)
    workflow = await sync_to_async(project.workflows.first)()
    st_ids = [s.id for s in await _list_workflow_statuses(workflow=workflow)]

    statuses = [st_ids[0], NOT_EXISTING_UUID]
    statuses = await repositories.list_workflow_statuses_to_reorder(
        workflow_id=workflow.id, ids=statuses
    )
    assert len(statuses) == 1
    assert statuses[0].id == statuses[0].id


##########################################################
# list_workflow_status_neighbors
##########################################################


async def test_list_workflow_status_neighbors(project_template) -> None:
    project = await f.create_project(project_template)
    workflow = await sync_to_async(project.workflows.first)()
    statuses = await repositories.list_workflow_statuses(workflow_id=workflow.id)

    neighbors = await repositories.list_workflow_status_neighbors(
        status=statuses[0], workflow_id=workflow.id
    )
    assert neighbors.prev is None
    assert neighbors.next.id == statuses[1].id

    neighbors = await repositories.list_workflow_status_neighbors(
        status=statuses[1], workflow_id=workflow.id
    )
    assert neighbors.prev.id == statuses[0].id
    assert neighbors.next.id == statuses[2].id

    neighbors = await repositories.list_workflow_status_neighbors(
        status=statuses[3], workflow_id=workflow.id
    )
    assert neighbors.prev.id == statuses[2].id
    assert neighbors.next is None


##########################################################
# get_workflow_status
##########################################################


async def test_get_workflow_status_ok(project_template) -> None:
    project = await f.create_project(project_template)
    workflows = await _list_workflows(project=project)
    workflow = workflows[0]
    statuses = await _list_workflow_statuses(workflow=workflow)
    status = statuses[0]

    workflow_status = await repositories.get_workflow_status(
        status_id=status.id,
        filters={
            "workflow_id": workflow.id,
        },
    )
    assert workflow_status == status


async def test_get_project_without_workflow_statuses_ok(project_template) -> None:
    project = await f.create_project(project_template)
    workflows = await _list_workflows(project=project)

    with pytest.raises(WorkflowStatus.DoesNotExist):
        await repositories.get_workflow_status(
            status_id=NOT_EXISTING_UUID,
            filters={
                "workflow_id": workflows[0].id,
            },
        )


##########################################################
# update_workflow_status
##########################################################


async def test_update_workflow_status_ok(project_template) -> None:
    project = await f.create_project(project_template)
    workflows = await _list_workflows(project=project)
    workflow = workflows[0]
    statuses = await _list_workflow_statuses(workflow=workflow)
    status = statuses[0]
    new_status_name = "new status name"
    new_values = {"name": new_status_name}

    updated_status = await repositories.update_workflow_status(
        workflow_status=status, values=new_values
    )
    assert updated_status.name == new_status_name


async def test_bulk_update_workflow_statuses_ok(project_template) -> None:
    project = await f.create_project(project_template)
    workflow = await sync_to_async(project.workflows.first)()
    statuses = await repositories.list_workflow_statuses(workflow_id=workflow.id)

    order = 1
    for status in statuses:
        assert status.order == order
        order += 1

    order = 100
    for status in statuses:
        status.order = order
        order += 1

    await repositories.bulk_update_workflow_statuses(
        objs_to_update=statuses, fields_to_update=["order"]
    )

    new_statuses = await repositories.list_workflow_statuses(workflow_id=workflow.id)
    order = 100
    for status in new_statuses:
        assert status.order == order
        order += 1


#########################################################
# delete workflow status
##########################################################


async def test_delete_workflow_status_without_stories_ok(project_template) -> None:
    project = await f.create_project(project_template)
    workflow = await f.create_workflow(project=project)
    # the workflow status to delete (without containing stories)
    workflow_status = await f.create_workflow_status(workflow=workflow)

    delete_ret = await repositories.delete_workflow_status(status_id=workflow_status.id)
    assert delete_ret == 1


async def test_delete_workflow_status_with_stories_ok(project_template) -> None:
    project = await f.create_project(project_template)
    workflow = await f.create_workflow(project=project)
    # the workflow status to delete
    workflow_status = await f.create_workflow_status(workflow=workflow)
    # its two stories, that should also be deleted
    await f.create_story(status=workflow_status, workflow=workflow)
    await f.create_story(status=workflow_status, workflow=workflow)

    delete_ret = await repositories.delete_workflow_status(status_id=workflow_status.id)

    assert delete_ret == 3


##########################################################
# utils
##########################################################


@sync_to_async
def _list_workflows(project: Project) -> list[Workflow]:
    return list(project.workflows.all())


@sync_to_async
def _list_workflow_statuses(workflow: Workflow) -> list[WorkflowStatus]:
    return list(workflow.statuses.all())
