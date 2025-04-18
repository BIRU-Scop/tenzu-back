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

from pydantic import ConfigDict, field_validator
from pydantic_core.core_schema import ValidationInfo

from base.serializers import UUIDB64, BaseModel
from stories.stories.serializers import StorySummarySerializer
from workflows.serializers.nested import (
    WorkflowNestedSerializer,
    WorkflowStatusNestedSerializer,
)


class WorkflowSerializer(BaseModel):
    id: UUIDB64
    project_id: UUIDB64
    name: str
    slug: str
    order: int
    statuses: list[WorkflowStatusNestedSerializer]
    model_config = ConfigDict(from_attributes=True)


class DeleteWorkflowSerializer(BaseModel):
    id: UUIDB64
    name: str
    slug: str
    order: int
    statuses: list[WorkflowStatusNestedSerializer]
    stories: list[StorySummarySerializer]
    model_config = ConfigDict(from_attributes=True)


class WorkflowStatusSerializer(BaseModel):
    id: UUIDB64
    name: str
    color: int
    order: int
    workflow: WorkflowNestedSerializer
    model_config = ConfigDict(from_attributes=True)


class ReorderSerializer(BaseModel):
    place: str
    status: UUIDB64
    model_config = ConfigDict(from_attributes=True)


class ReorderWorkflowStatusesSerializer(BaseModel):
    workflow: WorkflowNestedSerializer
    statuses: list[UUIDB64]
    reorder: ReorderSerializer | None = None
    model_config = ConfigDict(from_attributes=True)
