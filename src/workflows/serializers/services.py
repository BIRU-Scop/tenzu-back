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

from typing import Any
from uuid import UUID

from stories.stories.serializers import StorySummarySerializer
from workflows.models import Workflow, WorkflowStatus
from workflows.serializers import (
    DeleteWorkflowSerializer,
    ReorderWorkflowStatusesSerializer,
    WorkflowSerializer,
)


def serialize_workflow(
    workflow: Workflow, workflow_statuses: list[WorkflowStatus] = []
) -> WorkflowSerializer:
    return WorkflowSerializer(
        id=workflow.id,
        project_id=workflow.project_id,
        name=workflow.name,
        slug=workflow.slug,
        order=workflow.order,
        statuses=workflow_statuses,
    )


def serialize_delete_workflow_detail(
    workflow: Workflow,
    workflow_statuses: list[WorkflowStatus] = [],
    workflow_stories: list[StorySummarySerializer] = [],
) -> DeleteWorkflowSerializer:
    return DeleteWorkflowSerializer(
        id=workflow.id,
        name=workflow.name,
        slug=workflow.slug,
        order=workflow.order,
        statuses=workflow_statuses,
        stories=workflow_stories,
    )


def serialize_reorder_workflow_statuses(
    workflow: Workflow, status_ids: list[UUID], reorder: dict[str, Any] | None = None
) -> ReorderWorkflowStatusesSerializer:
    return ReorderWorkflowStatusesSerializer(
        workflow=workflow, status_ids=status_ids, reorder=reorder
    )
