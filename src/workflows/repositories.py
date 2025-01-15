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

# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2023-present Kaleidos INC

from decimal import Decimal
from typing import Any, Literal, TypedDict
from uuid import UUID

from asgiref.sync import sync_to_async

from base.db.models import Count, QuerySet
from base.repositories import neighbors as neighbors_repositories
from base.repositories.neighbors import Neighbor
from projects.projects.models import Project, ProjectTemplate
from workflows.models import Workflow, WorkflowStatus

##########################################################
# Workflow - filters and querysets
##########################################################


class WorkflowFilters(TypedDict, total=False):
    id: UUID
    slug: str
    project_id: UUID


WorkflowSelectRelated = list[Literal["project", "workspace"]]


WorkflowPrefetchRelated = list[Literal["statuses",]]


WorkflowOrderBy = list[Literal["order", "-order"]]


##########################################################
# Workflow - create workflow
##########################################################


def create_workflow_sync(
    name: str,
    slug: str,
    order: Decimal,
    project: Project,
) -> Workflow:
    return Workflow.objects.create(
        name=name,
        slug=slug,
        order=order,
        project=project,
    )


async def create_workflow(
    name: str,
    order: Decimal,
    project: Project,
) -> Workflow:
    return await Workflow.objects.acreate(
        name=name,
        order=order,
        project=project,
    )


##########################################################
# Workflow - list workflows
##########################################################


@sync_to_async
def list_workflows(
    filters: WorkflowFilters = {},
    prefetch_related: WorkflowPrefetchRelated = ["statuses"],
    order_by: WorkflowOrderBy = ["order"],
) -> list[Workflow]:
    qs = (
        Workflow.objects.all()
        .filter(**filters)
        .prefetch_related(*prefetch_related)
        .order_by(*order_by)
    )

    return list(qs)


##########################################################
# Workflow - get workflow
##########################################################


async def get_workflow(
    filters: WorkflowFilters = {},
    select_related: WorkflowSelectRelated = [],
    prefetch_related: WorkflowPrefetchRelated = ["statuses"],
) -> Workflow | None:
    qs = (
        Workflow.objects.all()
        .filter(**filters)
        .select_related(*select_related)
        .prefetch_related(*prefetch_related)
    )

    try:
        return await qs.aget()
    except Workflow.DoesNotExist:
        return None


##########################################################
# Workflow - update workflow
##########################################################


@sync_to_async
def update_workflow(workflow: Workflow, values: dict[str, Any] = {}) -> Workflow:
    for attr, value in values.items():
        setattr(workflow, attr, value)

    workflow.save()
    return workflow


##########################################################
# Workflow - delete workflow
##########################################################


async def delete_workflow(filters: WorkflowFilters = {}) -> int:
    qs = Workflow.objects.all().filter(**filters)
    count, _ = await qs.adelete()
    return count


##########################################################
# WorkflowStatus - filters and querysets
##########################################################

DEFAULT_QUERYSET_WORKFLOW_STATUS = WorkflowStatus.objects.all()


class WorkflowStatusFilters(TypedDict, total=False):
    id: UUID
    ids: list[UUID]
    workflow_id: UUID
    workflow_slug: str
    project_id: UUID
    is_empty: bool


def _apply_filters_to_workflow_status_queryset(
    qs: QuerySet[WorkflowStatus],
    filters: WorkflowStatusFilters = {},
) -> QuerySet[WorkflowStatus]:
    filter_data = dict(filters.copy())

    if "ids" in filters:
        filter_data["id__in"] = filter_data.pop("ids")

    if "workflow_slug" in filter_data:
        filter_data["workflow__slug"] = filter_data.pop("workflow_slug")

    if "project_id" in filter_data:
        filter_data["workflow__project_id"] = filter_data.pop("project_id")

    if "is_empty" in filter_data:
        qs = qs.annotate(num_stories=Count("stories"))
        if filter_data.pop("is_empty"):
            filter_data["num_stories"] = 0
        else:
            filter_data["num_stories__gt"] = 0

    return qs.filter(**filter_data)


WorkflowStatusSelectRelated = list[
    Literal[
        "workflow",
        "project",
        "workspace",
    ]
]


def _apply_select_related_to_workflow_status_queryset(
    qs: QuerySet[WorkflowStatus],
    select_related: WorkflowStatusSelectRelated,
) -> QuerySet[WorkflowStatus]:
    select_related_data = []

    for key in select_related:
        if key == "project":
            select_related_data.append("workflow__project")
        elif key == "workspace":
            select_related_data.append("workflow__project__workspace")
        else:
            select_related_data.append(key)

    return qs.select_related(*select_related_data)


WorkflowStatusOrderBy = list[
    Literal[
        "order",
        "-order",
    ]
]


def _apply_order_by_to_workflow_status_queryset(
    qs: QuerySet[WorkflowStatus], order_by: WorkflowStatusOrderBy
) -> QuerySet[WorkflowStatus]:
    return qs.order_by(*order_by)


##########################################################
# WorkflowStatus - create workflow status
##########################################################


def create_workflow_status_sync(
    name: str,
    color: int,
    order: Decimal,
    workflow: Workflow,
) -> WorkflowStatus:
    return WorkflowStatus.objects.create(
        name=name,
        color=color,
        order=order,
        workflow=workflow,
    )


create_workflow_status = sync_to_async(create_workflow_status_sync)


##########################################################
# WorkflowStatus - list workflow statuses
##########################################################


@sync_to_async
def list_workflow_statuses(
    filters: WorkflowStatusFilters = {},
    order_by: WorkflowStatusOrderBy = ["order"],
    offset: int | None = None,
    limit: int | None = None,
) -> list[WorkflowStatus]:
    qs = _apply_filters_to_workflow_status_queryset(
        qs=DEFAULT_QUERYSET_WORKFLOW_STATUS, filters=filters
    )
    qs = _apply_order_by_to_workflow_status_queryset(qs=qs, order_by=order_by)

    if limit is not None and offset is not None:
        limit += offset

    return list(qs[offset:limit])


@sync_to_async
def list_workflow_statuses_to_reorder(
    filters: WorkflowStatusFilters = {},
) -> list[WorkflowStatus]:
    """
    This method is very similar to "list_workflow_statuses" except this has to keep
    the order of the input ids.
    """
    qs = _apply_filters_to_workflow_status_queryset(
        qs=DEFAULT_QUERYSET_WORKFLOW_STATUS, filters=filters
    )

    statuses = {s.id: s for s in qs}
    return [statuses[id] for id in filters["ids"] if statuses.get(id) is not None]


@sync_to_async
def list_workflow_status_neighbors(
    status: WorkflowStatus,
    filters: WorkflowStatusFilters = {},
) -> Neighbor[WorkflowStatus]:
    qs = _apply_filters_to_workflow_status_queryset(
        qs=DEFAULT_QUERYSET_WORKFLOW_STATUS, filters=filters
    )
    qs = _apply_order_by_to_workflow_status_queryset(qs=qs, order_by=["order"])

    return neighbors_repositories.get_neighbors_sync(obj=status, model_queryset=qs)


##########################################################
# WorkflowStatus - get workflow status
##########################################################


@sync_to_async
def get_workflow_status(
    filters: WorkflowStatusFilters = {},
    select_related: WorkflowStatusSelectRelated = [],
) -> WorkflowStatus | None:
    qs = _apply_filters_to_workflow_status_queryset(
        qs=DEFAULT_QUERYSET_WORKFLOW_STATUS, filters=filters
    )
    qs = _apply_select_related_to_workflow_status_queryset(
        qs=qs, select_related=select_related
    )

    try:
        return qs.get()
    except WorkflowStatus.DoesNotExist:
        return None


##########################################################
# WorkflowStatus - update workflow status
##########################################################


@sync_to_async
def update_workflow_status(
    workflow_status: WorkflowStatus, values: dict[str, Any] = {}
) -> WorkflowStatus:
    for attr, value in values.items():
        setattr(workflow_status, attr, value)

    workflow_status.save()
    return workflow_status


async def bulk_update_workflow_statuses(
    objs_to_update: list[WorkflowStatus], fields_to_update: list[str]
) -> None:
    await WorkflowStatus.objects.abulk_update(objs_to_update, fields_to_update)


##########################################################
# WorkflowStatus - delete workflow status
##########################################################


async def delete_workflow_status(filters: WorkflowStatusFilters = {}) -> int:
    qs = _apply_filters_to_workflow_status_queryset(
        qs=DEFAULT_QUERYSET_WORKFLOW_STATUS, filters=filters
    )
    count, _ = await qs.adelete()
    return count


##########################################################
# WorkflowStatus - misc
##########################################################


def apply_default_workflow_statuses_sync(
    template: ProjectTemplate, workflow: Workflow
) -> None:
    for status in template.workflow_statuses:
        create_workflow_status_sync(
            name=status["name"],
            color=status["color"],
            order=status["order"],
            workflow=workflow,
        )


apply_default_workflow_statuses = sync_to_async(apply_default_workflow_statuses_sync)
