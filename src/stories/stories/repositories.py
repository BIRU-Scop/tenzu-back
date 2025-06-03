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
from typing import Any, Final, Literal, TypedDict
from uuid import UUID

from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import Q, QuerySet

from base.occ import repositories as occ_repositories
from base.repositories import neighbors as neighbors_repositories
from base.repositories.neighbors import Neighbor
from stories.stories.models import Story

##########################################################
# filters and querysets
##########################################################

ASSIGNEE_IDS_ANNOTATION = ArrayAgg(
    "assignees",
    order_by="-story_assignments__created_at",
    filter=Q(assignees__isnull=False),
    default=[],
)


class StoryFilters(TypedDict, total=False):
    project_id: UUID
    workflow_id: UUID
    workflow__slug: str
    status_id: UUID
    order__gt: int
    ref__in: list[int]


StorySelectRelated = list[
    Literal[
        "created_by",
        "project",
        "workflow",
        "status",
        "project__workspace",
        "title_updated_by",
        "description_updated_by",
    ]
    | None
]


StoryOrderBy = list[
    Literal[
        "order",
        "-order",
        "status",
    ]
]


##########################################################
# create story
##########################################################


async def create_story(
    title: str,
    project_id: UUID,
    workflow_id: UUID,
    status_id: UUID,
    user_id: UUID,
    order: Decimal,
    description: str | None = None,
) -> Story:
    return await Story.objects.acreate(
        title=title,
        description=description,
        project_id=project_id,
        workflow_id=workflow_id,
        status_id=status_id,
        created_by_id=user_id,
        order=order,
    )


##########################################################
# list stories
##########################################################


def list_stories_qs(
    filters: StoryFilters = {},
    excludes: StoryFilters = {},
    order_by: StoryOrderBy = None,
    offset: int | None = None,
    limit: int | None = None,
    select_related: StorySelectRelated = [None],
) -> QuerySet[Story]:
    qs = (
        Story.objects.all()
        .filter(**filters)
        .exclude(**excludes)
        .select_related(*select_related)
    )
    if order_by is not None:
        # only replace default order_by if defined
        qs = qs.order_by(*order_by)

    if limit is not None and offset is not None:
        limit += offset

    return qs[offset:limit]


##########################################################
# get story
##########################################################


async def get_story(
    ref: int,
    filters: StoryFilters = {},
    select_related: StorySelectRelated = ["status"],
    get_assignees=False,
) -> Story:
    annotations = {"assignee_ids": ASSIGNEE_IDS_ANNOTATION} if get_assignees else {}
    qs = (
        Story.objects.all()
        .filter(ref=ref, **filters)
        .select_related(*select_related)
        .annotate(**annotations)
    )
    return await qs.aget()


##########################################################
# update stories
##########################################################

PROTECTED_ATTRS_ON_UPDATE: Final[list[str]] = [
    "title",
    "description",
]


async def update_story(
    id: UUID, current_version: int | None = None, values: dict[str, Any] = {}
) -> bool:
    return await occ_repositories.update(
        model_class=Story,
        id=id,
        current_version=current_version,
        values=values,
        protected_attrs=PROTECTED_ATTRS_ON_UPDATE,
    )


async def bulk_update_stories(
    objs_to_update: list[Story], fields_to_update: list[str]
) -> None:
    await Story.objects.abulk_update(objs_to_update, fields_to_update)


##########################################################
# delete story
##########################################################


async def delete_story(story_id: UUID) -> int:
    qs = Story.objects.all().filter(id=story_id)
    count, _ = await qs.adelete()
    return count


##########################################################
# misc
##########################################################


async def list_story_neighbors(
    story: Story, filters: StoryFilters = {}, excludes: dict = {}
) -> Neighbor[Story]:
    qs = (
        Story.objects.all()
        .filter(**filters)
        .exclude(**excludes)
        .order_by("status", "order")
    )

    return await neighbors_repositories.get_neighbors(obj=story, model_queryset=qs)


async def list_stories_to_reorder(
    ref__in: list[int], filters: StoryFilters = {}
) -> list[Story]:
    """
    This method keeps the order of the input references.
    """
    qs = (
        Story.objects.all()
        .filter(ref__in=ref__in, **filters)
        .select_related("project")
        .annotate(assignee_ids=ASSIGNEE_IDS_ANNOTATION)
    )

    # keep ref order
    order = {ref: index for index, ref in enumerate(ref__in)}
    return sorted([s async for s in qs], key=lambda s: order[s.ref])


async def bulk_update_workflow_to_stories(
    statuses_ids: list[UUID], old_workflow_id: UUID, new_workflow_id: UUID
) -> None:
    await Story.objects.filter(
        status_id__in=statuses_ids, workflow_id=old_workflow_id
    ).aupdate(workflow_id=new_workflow_id)
