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
from django.db.models import Count

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


WorkflowSelectRelated = list[Literal["project", "project__workspace"]]


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


class WorkflowStatusFilters(TypedDict, total=False):
    workflow_id: UUID
    workflow__slug: str
    workflow__project_id: UUID


WorkflowStatusSelectRelated = list[
    Literal[
        "workflow",
        "workflow__project",
        "workflow__project__workspace",
    ]
]


WorkflowStatusOrderBy = list[
    Literal[
        "order",
        "-order",
    ]
]


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


async def list_workflow_statuses(
    workflow_id: UUID,
    is_empty: bool | None = None,
    order_by: WorkflowStatusOrderBy = ["order"],
    offset: int | None = None,
    limit: int | None = None,
) -> list[WorkflowStatus]:
    qs = (
        WorkflowStatus.objects.all().filter(workflow_id=workflow_id).order_by(*order_by)
    )

    if is_empty is not None:
        qs = qs.annotate(num_stories=Count("stories"))
        qs = qs.filter(num_stories=0) if is_empty else qs.filter(num_stories__gt=0)

    if limit is not None and offset is not None:
        limit += offset

    return [s async for s in qs[offset:limit]]


async def list_workflow_statuses_to_reorder(
    workflow_id: UUID,
    ids: list[UUID],
) -> list[WorkflowStatus]:
    """
    This method is very similar to "list_workflow_statuses" except this has to keep
    the order of the input ids.
    """
    qs = WorkflowStatus.objects.all().filter(workflow_id=workflow_id, id__in=ids)

    # keep ids order
    order = {ref: index for index, ref in enumerate(ids)}
    return sorted([s async for s in qs], key=lambda s: order[s.id])


@sync_to_async
def list_workflow_status_neighbors(
    workflow_id: UUID,
    status: WorkflowStatus,
) -> Neighbor[WorkflowStatus]:
    qs = WorkflowStatus.objects.all().filter(workflow_id=workflow_id).order_by("order")

    return neighbors_repositories.get_neighbors_sync(obj=status, model_queryset=qs)


##########################################################
# WorkflowStatus - get workflow status
##########################################################


async def get_workflow_status(
    status_id: UUID,
    filters: WorkflowStatusFilters = {},
    select_related: WorkflowStatusSelectRelated = [],
) -> WorkflowStatus | None:
    qs = WorkflowStatus.objects.all().filter(**filters).select_related(*select_related)

    try:
        return await qs.aget(id=status_id)
    except WorkflowStatus.DoesNotExist:
        return None


##########################################################
# WorkflowStatus - update workflow status
##########################################################


async def update_workflow_status(
    workflow_status: WorkflowStatus, values: dict[str, Any] = {}
) -> WorkflowStatus:
    for attr, value in values.items():
        setattr(workflow_status, attr, value)

    await workflow_status.asave()
    return workflow_status


async def bulk_update_workflow_statuses(
    objs_to_update: list[WorkflowStatus], fields_to_update: list[str]
) -> None:
    await WorkflowStatus.objects.abulk_update(objs_to_update, fields_to_update)


##########################################################
# WorkflowStatus - delete workflow status
##########################################################


async def delete_workflow_status(
    status_id: UUID,
) -> int:
    qs = WorkflowStatus.objects.all().filter(id=status_id)
    count, _ = await qs.adelete()
    return count


##########################################################
# WorkflowStatus - misc
##########################################################


async def apply_default_workflow_statuses(
    template: ProjectTemplate, workflow: Workflow
) -> None:
    statuses = [
        WorkflowStatus(
            name=status["name"],
            color=status["color"],
            order=status["order"],
            workflow=workflow,
        )
        for status in template.workflow_statuses
    ]
    await WorkflowStatus.objects.abulk_create(statuses)
