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

from base.repositories.neighbors import Neighbor
from stories.stories.models import Story
from stories.stories.serializers import (
    ReorderStoriesSerializer,
    StoryDetailSerializer,
    StorySummarySerializer,
)
from users.models import User
from workflows.models import WorkflowStatus


def serialize_story_detail(
    story: Story,
    neighbors: Neighbor[Story],
    assignees: list[User] = [],
) -> StoryDetailSerializer:
    return StoryDetailSerializer(
        ref=story.ref,
        title=story.title,
        description=story.description,
        status_id=story.status_id,
        status=story.status,
        workflow_id=story.workflow_id,
        project_id=story.project_id,
        workflow=story.workflow,
        created_by=story.created_by,
        created_at=story.created_at,
        version=story.version,
        assignees=assignees,
        prev=neighbors.prev,
        next=neighbors.next,
        title_updated_by=story.title_updated_by,
        title_updated_at=story.title_updated_at,
        description_updated_by=story.description_updated_by,
        description_updated_at=story.description_updated_at,
    )


def serialize_story_list(
    story: Story,
    assignees: list[User] = [],
) -> StorySummarySerializer:
    return StorySummarySerializer(
        ref=story.ref,
        title=story.title,
        workflow_id=story.workflow_id,
        project_id=story.project_id,
        status_id=story.status_id,
        status=story.status,
        version=story.version,
        assignees=assignees,
    )


def serialize_reorder_story(
    status: WorkflowStatus, stories: list[int], reorder: dict[str, Any] | None = None
) -> ReorderStoriesSerializer:
    return ReorderStoriesSerializer(
        status_id=status.id, status=status, stories=stories, reorder=reorder
    )
