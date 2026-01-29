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

from base.serializers import BaseModel
from workflows.serializers import (
    ReorderWorkflowStatusesSerializer,
    WorkflowNestedSerializer,
    WorkflowSerializer,
    WorkflowStatusSerializer,
)


class CreateWorkflowContent(BaseModel):
    workflow: WorkflowSerializer


class UpdateWorkflowContent(BaseModel):
    workflow: WorkflowSerializer


class DeleteWorkflowContent(BaseModel):
    workflow: WorkflowNestedSerializer
    target_workflow: WorkflowNestedSerializer | None = None


class CreateWorkflowStatusContent(BaseModel):
    workflow_status: WorkflowStatusSerializer


class UpdateWorkflowStatusContent(BaseModel):
    workflow_status: WorkflowStatusSerializer


class ReorderWorkflowStatusesContent(BaseModel):
    reorder: ReorderWorkflowStatusesSerializer


class DeleteWorkflowStatusContent(BaseModel):
    workflow_status: WorkflowStatusSerializer
    target_status: WorkflowStatusSerializer | None = None
