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

from typing import Literal, TypedDict
from uuid import UUID

from asgiref.sync import sync_to_async
from django.db.models import QuerySet

from stories.assignments.models import StoryAssignment
from stories.stories.models import Story
from users.models import User

##########################################################
# filters and querysets
##########################################################

DEFAULT_QUERYSET = StoryAssignment.objects.all()


class StoryAssignmentFilters(TypedDict, total=False):
    id: UUID
    ref: int
    project_id: UUID
    story_id: UUID
    username: str
    role_id: UUID


def _apply_filters_to_queryset(
    qs: QuerySet[StoryAssignment],
    filters: StoryAssignmentFilters = {},
) -> QuerySet[StoryAssignment]:
    filter_data = dict(filters.copy())

    if "ref" in filter_data:
        filter_data["story__ref"] = filter_data.pop("ref")

    if "project_id" in filter_data:
        filter_data["story__project_id"] = filter_data.pop("project_id")

    if "username" in filter_data:
        filter_data["user__username"] = filter_data.pop("username")

    if "role_id" in filter_data:
        filter_data["user__project_memberships__role_id"] = filter_data.pop("role_id")

    return qs.filter(**filter_data)


StoryAssignmentSelectRelated = list[
    Literal[
        "story",
        "user",
        "project",
        "workspace",
    ]
]


def _apply_select_related_to_queryset(
    qs: QuerySet[StoryAssignment],
    select_related: StoryAssignmentSelectRelated,
) -> QuerySet[StoryAssignment]:
    select_related_data = []
    for key in select_related:
        if key == "project":
            select_related_data.append("story__project")
        elif key == "workspace":
            select_related_data.append("story__project__workspace")
        else:
            select_related_data.append(key)

    return qs.select_related(*select_related_data)


##########################################################
# create story assignment
##########################################################


@sync_to_async
def create_story_assignment(story: Story, user: User) -> tuple[StoryAssignment, bool]:
    return StoryAssignment.objects.select_related("story", "user").get_or_create(
        story=story, user=user
    )


##########################################################
# get story assignment
##########################################################


@sync_to_async
def get_story_assignment(
    filters: StoryAssignmentFilters = {},
    select_related: StoryAssignmentSelectRelated = ["story", "user"],
) -> StoryAssignment | None:
    qs = _apply_filters_to_queryset(qs=DEFAULT_QUERYSET, filters=filters)
    qs = _apply_select_related_to_queryset(qs=qs, select_related=select_related)

    try:
        return qs.get()
    except StoryAssignment.DoesNotExist:
        return None


##########################################################
# delete story assignment
##########################################################


@sync_to_async
def delete_stories_assignments(filters: StoryAssignmentFilters = {}) -> int:
    qs = _apply_filters_to_queryset(qs=DEFAULT_QUERYSET, filters=filters)
    count, _ = qs.delete()
    return count
