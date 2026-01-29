# -*- coding: utf-8 -*-
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

from events import events_manager
from projects.projects.models import Project
from workflows.events.content import (
    CreateWorkflowContent,
    CreateWorkflowStatusContent,
    DeleteWorkflowContent,
    DeleteWorkflowStatusContent,
    ReorderWorkflowStatusesContent,
    UpdateWorkflowContent,
    UpdateWorkflowStatusContent,
)
from workflows.models import WorkflowStatus
from workflows.serializers import (
    ReorderWorkflowStatusesSerializer,
    WorkflowNestedSerializer,
    WorkflowSerializer,
)

CREATE_WORKFLOW = "workflows.create"
UPDATE_WORKFLOW = "workflows.update"
DELETE_WORKFLOW = "workflows.delete"
CREATE_WORKFLOW_STATUS = "workflowstatuses.create"
UPDATE_WORKFLOW_STATUS = "workflowstatuses.update"
REORDER_WORKFLOW_STATUS = "workflowstatuses.reorder"
DELETE_WORKFLOW_STATUS = "workflowstatuses.delete"


async def emit_event_when_workflow_is_created(
    project: Project, workflow: WorkflowSerializer
) -> None:
    await events_manager.publish_on_project_channel(
        project=project,
        type=CREATE_WORKFLOW,
        content=CreateWorkflowContent(workflow=workflow),
    )


async def emit_event_when_workflow_is_updated(
    project: Project, workflow: WorkflowSerializer
) -> None:
    await events_manager.publish_on_project_channel(
        project=project,
        type=UPDATE_WORKFLOW,
        content=UpdateWorkflowContent(
            workflow=workflow,
        ),
    )


async def emit_event_when_workflow_is_deleted(
    project: Project,
    workflow: WorkflowNestedSerializer,
    target_workflow: WorkflowNestedSerializer | None,
) -> None:
    await events_manager.publish_on_project_channel(
        project=project,
        type=DELETE_WORKFLOW,
        content=DeleteWorkflowContent(
            workflow=workflow,
            target_workflow=target_workflow,
        ),
    )


async def emit_event_when_workflow_status_is_created(
    project: Project, workflow_status: WorkflowStatus
) -> None:
    await events_manager.publish_on_project_channel(
        project=project,
        type=CREATE_WORKFLOW_STATUS,
        content=CreateWorkflowStatusContent(workflow_status=workflow_status),
    )


async def emit_event_when_workflow_status_is_updated(
    project: Project, workflow_status: WorkflowStatus
) -> None:
    await events_manager.publish_on_project_channel(
        project=project,
        type=UPDATE_WORKFLOW_STATUS,
        content=UpdateWorkflowStatusContent(workflow_status=workflow_status),
    )


async def emit_event_when_workflow_statuses_are_reordered(
    project: Project, reorder: ReorderWorkflowStatusesSerializer
) -> None:
    await events_manager.publish_on_project_channel(
        project=project,
        type=REORDER_WORKFLOW_STATUS,
        content=ReorderWorkflowStatusesContent(reorder=reorder),
    )


async def emit_event_when_workflow_status_is_deleted(
    project: Project,
    workflow_status: WorkflowStatus,
    target_status: WorkflowStatus | None,
) -> None:
    await events_manager.publish_on_project_channel(
        project=project,
        type=DELETE_WORKFLOW_STATUS,
        content=DeleteWorkflowStatusContent(
            workflow_status=workflow_status,
            target_status=target_status,
        ),
    )
