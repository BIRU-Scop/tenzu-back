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

from datetime import datetime

from pydantic import ConfigDict

from base.serializers import UUIDB64, BaseModel
from stories.stories.serializers.nested import StoryNeighborSerializer
from users.serializers.nested import UserNestedSerializer
from workflows.serializers.nested import (
    WorkflowNestedSerializer,
    WorkflowStatusNestedSerializer,
)


class StorySummarySerializer(BaseModel):
    ref: int
    title: str
    status_id: UUIDB64
    workflow_id: UUIDB64
    project_id: UUIDB64
    version: int
    assignees: list[UserNestedSerializer] | None = None
    model_config = ConfigDict(
        from_attributes=True,
    )


class StoryDetailSerializer(BaseModel):
    ref: int
    title: str
    description: str | None = None
    status_id: UUIDB64
    status: WorkflowStatusNestedSerializer
    workflow_id: UUIDB64
    project_id: UUIDB64
    workflow: WorkflowNestedSerializer
    created_by: UserNestedSerializer | None = None
    created_at: datetime
    prev: StoryNeighborSerializer | None = None
    next: StoryNeighborSerializer | None = None
    version: int
    assignees: list[UserNestedSerializer]
    title_updated_by: UserNestedSerializer | None = None
    title_updated_at: datetime | None = None
    description_updated_by: UserNestedSerializer | None = None
    description_updated_at: datetime | None = None


class ReorderSerializer(BaseModel):
    place: str
    ref: int
    model_config = ConfigDict(from_attributes=True)


class ReorderStoriesSerializer(BaseModel):
    status_id: UUIDB64
    status: WorkflowStatusNestedSerializer
    stories: list[int]
    reorder: ReorderSerializer | None = None
    model_config = ConfigDict(from_attributes=True)
