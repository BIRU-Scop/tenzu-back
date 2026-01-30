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

from decimal import Decimal
from typing import Any, cast
from uuid import UUID

from django.conf import settings

from commons.ordering import DEFAULT_ORDER_OFFSET, calculate_offset
from commons.utils import transaction_atomic_async, transaction_on_commit_async
from projects.projects import repositories as projects_repositories
from projects.projects import services as projects_services
from projects.projects.models import Project, ProjectTemplate
from stories.stories import repositories as stories_repositories
from stories.stories import services as stories_services
from users.models import User
from workflows import events as workflows_events
from workflows import repositories as workflows_repositories
from workflows.models import Workflow, WorkflowStatus
from workflows.serializers import (
    ReorderWorkflowStatusesSerializer,
    WorkflowNestedSerializer,
    WorkflowSerializer,
)
from workflows.services import exceptions as ex

##########################################################
# create workflow
##########################################################


@transaction_atomic_async
async def create_workflow(project: Project, name: str) -> WorkflowSerializer:
    workflow_orders = [
        w
        async for w in workflows_repositories.list_workflows_qs(
            filters={"project_id": project.id}, order_by=["-order"]
        ).values_list("order", flat=True)
    ]

    # validate num workflows
    num_workflows = len(workflow_orders) if workflow_orders else 0
    if num_workflows >= settings.MAX_NUM_WORKFLOWS:
        raise ex.MaxNumWorkflowCreatedError("Maximum number of workflows is reached")

    # calculate order
    order = DEFAULT_ORDER_OFFSET + (workflow_orders[0] if workflow_orders else 0)

    workflow = await workflows_repositories.create_workflow(
        project=project, name=name, order=order
    )
    if not workflow_orders:
        await projects_repositories.update_project(
            project,
            values={
                "landing_page": projects_services.get_landing_page_for_workflow(
                    workflow.slug
                )
            },
        )

    # apply default workflow statuses from project template
    try:
        template = await projects_repositories.get_project_template(
            filters={"slug": settings.DEFAULT_PROJECT_TEMPLATE}
        )
    except ProjectTemplate.DoesNotExist as e:
        raise Exception(
            f"Default project template '{settings.DEFAULT_PROJECT_TEMPLATE}' not found. "
            "Try to run migrations again and check if the error persist."
        ) from e

    workflow_statuses = await workflows_repositories.apply_default_workflow_statuses(
        template=template, workflow=workflow
    )
    serialized_workflow = WorkflowSerializer(
        id=workflow.id,
        project_id=workflow.project_id,
        name=workflow.name,
        slug=workflow.slug,
        order=workflow.order,
        statuses=workflow_statuses,
    )

    # emit event
    await transaction_on_commit_async(
        workflows_events.emit_event_when_workflow_is_created
    )(project=workflow.project, workflow=serialized_workflow)

    return serialized_workflow


##########################################################
# list workflows
##########################################################


async def list_workflows(project_id: UUID) -> list[Workflow]:
    workflows = [
        w
        async for w in workflows_repositories.list_workflows_qs(
            filters={
                "project_id": project_id,
            },
            prefetch_related=["statuses"],
        )
    ]

    return workflows


##########################################################
# get workflow
##########################################################


async def get_workflow_by_slug(project_id: UUID, workflow_slug: str) -> Workflow | None:
    return await workflows_repositories.get_workflow(
        filters={
            "project_id": project_id,
            "slug": workflow_slug,
        },
        select_related=[
            "project",
        ],
    )


async def get_workflow_by_id(workflow_id: UUID) -> Workflow | None:
    return await workflows_repositories.get_workflow(
        filters={
            "id": workflow_id,
        },
        select_related=[
            "project",
        ],
    )


##########################################################
# update workflow
##########################################################


@transaction_atomic_async
async def update_workflow(
    workflow: Workflow, updated_by: User, values: dict[str, Any] = {}
) -> Workflow:
    previous_slug = workflow.slug
    updated_workflow = await workflows_repositories.update_workflow(
        workflow=workflow, values=values
    )

    if (
        previous_slug != updated_workflow.slug
        and workflow.project.landing_page.endswith(f"/{previous_slug}")
    ):
        await projects_services.update_project_landing_page(
            workflow.project, updated_by, updated_workflow.slug
        )

    # Emit event
    await transaction_on_commit_async(
        workflows_events.emit_event_when_workflow_is_updated
    )(
        project=workflow.project,
        workflow=updated_workflow,
    )

    return updated_workflow


##########################################################
# delete workflow
##########################################################


@transaction_atomic_async
async def delete_workflow(
    workflow: Workflow, deleted_by: User, target_workflow_id: UUID | None = None
) -> bool:
    """
    This method deletes a workflow, providing the option to first migrate its workflow statuses to another workflow
    in the same project.

    :param workflow: the workflow to delete
    :param deleted_by: the user which has deleted this workflow
    :param target_workflow_id: the workflow slug to which move their statuses from the workflow being deleted
        - if not received, the workflow, statuses and its contained stories will be deleted
        - if received, the workflow will be deleted but its statuses and stories won't (they will be appended to the
         last status of the specified workflow).
    :return: bool
    """
    target_workflow = None
    if target_workflow_id:
        try:
            target_workflow = await workflows_repositories.get_workflow(
                filters={
                    "project_id": workflow.project_id,
                    "id": target_workflow_id,
                },
                select_related=[
                    "project",
                ],
            )
        except Workflow.DoesNotExist as e:
            raise ex.NonExistingMoveToWorkflow(
                f"The workflow '{target_workflow_id}' doesn't exist in project {workflow.project_id}"
            ) from e
        if target_workflow.id == workflow.id:
            raise ex.SameMoveToWorkflow(
                "The to-be-deleted workflow and the target-workflow cannot be the same"
            )

        statuses_to_move = await workflows_repositories.list_workflow_statuses(
            workflow_id=workflow.id,
            is_empty=False,
            order_by=["order"],
        )

        if statuses_to_move:
            target_workflow_statuses = list(target_workflow.statuses.all())
            #  no statuses in the target_workflow (no valid anchor). The order of the statuses will be preserved
            if not target_workflow_statuses:
                await reorder_workflow_statuses(
                    target_workflow=target_workflow,
                    status_ids=[status.id for status in statuses_to_move],
                    reorder=None,
                    source_workflow=workflow,
                )
            # existing statuses in the target_workflow. The anchor status will be the last one
            else:
                await reorder_workflow_statuses(
                    target_workflow=target_workflow,
                    status_ids=[status.id for status in statuses_to_move],
                    reorder={
                        "place": "after",
                        "status_id": target_workflow_statuses[-1].id,
                    },
                    source_workflow=workflow,
                )

    deleted = await workflows_repositories.delete_workflow(filters={"id": workflow.id})

    if deleted > 0:
        if workflow.project.landing_page.endswith(f"/{workflow.slug}"):
            await projects_services.update_project_landing_page(
                workflow.project, deleted_by
            )

        await transaction_on_commit_async(
            workflows_events.emit_event_when_workflow_is_deleted
        )(
            project=workflow.project,
            workflow=WorkflowNestedSerializer(
                id=workflow.id,
                name=workflow.name,
                slug=workflow.slug,
                project_id=workflow.project_id,
            ),
            target_workflow=target_workflow,
        )
        return True

    return False


##########################################################
# create workflow status
##########################################################


async def create_workflow_status(
    name: str, color: int, workflow: Workflow
) -> WorkflowStatus:
    # Create workflow status
    workflow_status = await workflows_repositories.create_workflow_status(
        name=name, color=color, workflow=workflow
    )

    # Emit event
    await workflows_events.emit_event_when_workflow_status_is_created(
        project=workflow.project, workflow_status=workflow_status
    )

    return workflow_status


##########################################################
# get workflow status
##########################################################


async def get_workflow_status(status_id: UUID) -> WorkflowStatus | None:
    return await workflows_repositories.get_workflow_status(
        status_id=status_id,
        select_related=[
            "workflow",
            "workflow__project",
        ],
    )


##########################################################
# update workflow status
##########################################################


async def update_workflow_status(
    workflow_status: WorkflowStatus, values: dict[str, Any] = {}
) -> WorkflowStatus:
    if not values:
        return workflow_status

    if "name" in values and values["name"] is None:
        raise ex.TenzuValidationError("Name cannot be null")

    updated_status = await workflows_repositories.update_workflow_status(
        workflow_status=workflow_status, values=values
    )

    await workflows_events.emit_event_when_workflow_status_is_updated(
        project=workflow_status.project, workflow_status=updated_status
    )

    return updated_status


##########################################################
# update reorder workflow statuses
##########################################################


async def _calculate_offset(
    workflow: Workflow,
    total_statuses_to_reorder: int,
    reorder_reference_status: WorkflowStatus,
    reorder_place: str,
    reordered_statuses: list[UUID] = None,
) -> tuple[int, int]:
    total_slots = total_statuses_to_reorder + 1

    neighbors = await workflows_repositories.list_workflow_status_neighbors(
        workflow_id=workflow.id,
        status=reorder_reference_status,
        excludes={"id__in": reordered_statuses}
        if reordered_statuses is not None
        else {},
    )

    return calculate_offset(
        reorder_reference_status, reorder_place, total_slots, neighbors
    )


@transaction_atomic_async
async def reorder_workflow_statuses(
    target_workflow: Workflow,
    status_ids: list[UUID],
    reorder: dict[str, Any] | None,
    source_workflow: Workflow | None = None,
) -> None:
    """
    Reorder the statuses from a workflow to another (can be the same), before or after an existing status
    (anchor) when a reorder criteria is provided, or preserving its original order when not provided.
    :param target_workflow: the destination workflow for the statuses being reordered
    :param status_ids: the statuses id's to reorder (move) in the "target_workflow"
    :param reorder: reorder["status"] anchor workflow status's id, reorder["place"]: position strategy ["before","after]
        None will mean there's no anchor status preserving their original order
    :param source_workflow: Workflow containing the statuses to reorder.
        None will mean the "source_workflow" and the "target_workflow" are the same
    :return:
    """
    if not source_workflow:
        source_workflow = target_workflow

    statuses_to_reorder = (
        await workflows_repositories.list_workflow_statuses_to_reorder(
            workflow_id=source_workflow.id, ids=status_ids
        )
    )
    if len(statuses_to_reorder) < len(status_ids):
        raise ex.InvalidWorkflowStatusError(
            "One or more statuses don't exist in this workflow"
        )

    statuses_to_update = []

    if not reorder:
        if source_workflow == target_workflow:
            raise ex.NonExistingMoveToStatus("Reorder criteria required")
        else:
            for i, status in enumerate(statuses_to_reorder):
                status.workflow = target_workflow
                statuses_to_update.append(status)
    # position statuses according to this anchor status
    elif reorder:
        # check anchor workflow status exists
        try:
            reorder_reference_status = await workflows_repositories.get_workflow_status(
                status_id=reorder["status_id"],
                filters={
                    "workflow_id": target_workflow.id,
                },
            )
        except WorkflowStatus.DoesNotExist as e:
            # re-ordering in the same workflow must have a valid anchor status
            raise ex.InvalidWorkflowStatusError(
                f"Status {reorder['status_id']} doesn't exist in this workflow"
            ) from e

        if reorder["status_id"] in status_ids:
            raise ex.InvalidWorkflowStatusError(
                f"Status {reorder['status_id']} should not be part of the statuses to reorder"
            )
        reorder_place = reorder["place"]
        # calculate offset
        offset, pre_order = await _calculate_offset(
            workflow=target_workflow,
            total_statuses_to_reorder=len(statuses_to_reorder),
            reorder_reference_status=reorder_reference_status,
            reorder_place=reorder_place,
            reordered_statuses=status_ids,
        )
        if offset == 0:
            # There is not enough space left between the stories where stories_to_reorder need to be inserted
            # We need to move more stories, this should happen very infrequently thanks to the offset
            after_statuses = await workflows_repositories.list_workflow_statuses(
                workflow_id=target_workflow.id,
                filters={
                    "order__gt": pre_order,
                },
                excludes={"id__in": status_ids},
                order_by=["order"],
            )
            total_slots = len(statuses_to_reorder) + 1
            for nearby_after_story in after_statuses:
                if nearby_after_story.order - pre_order < total_slots:
                    statuses_to_reorder.append(nearby_after_story)
                    total_slots += 1
                else:
                    offset = (nearby_after_story.order - pre_order) // total_slots
                    break
            else:
                offset = DEFAULT_ORDER_OFFSET
        # update workflow statuses
        for i, status in enumerate(statuses_to_reorder):
            status.order = pre_order + (offset * (i + 1))
            status.workflow = target_workflow
            statuses_to_update.append(status)

    # save status
    await workflows_repositories.bulk_update_workflow_statuses(
        objs_to_update=statuses_to_update, fields_to_update=["order", "workflow"]
    )

    if source_workflow != target_workflow and statuses_to_reorder:
        # update the workflow to the moved stories
        await stories_repositories.bulk_update_workflow_to_stories(
            statuses_ids=status_ids,
            old_workflow_id=source_workflow.id,
            new_workflow_id=target_workflow.id,
        )

    reorder_status_serializer = ReorderWorkflowStatusesSerializer(
        workflow=target_workflow, status_ids=status_ids, reorder=reorder
    )

    # event
    await transaction_on_commit_async(
        workflows_events.emit_event_when_workflow_statuses_are_reordered
    )(project=target_workflow.project, reorder=reorder_status_serializer)


##########################################################
# delete workflow status
##########################################################


@transaction_atomic_async
async def delete_workflow_status(
    workflow_status: WorkflowStatus, deleted_by: User, target_status_id: UUID | None
) -> bool:
    """
    This method deletes a workflow status, providing the option to first migrate its stories to another workflow
    status of the same workflow.

    :param deleted_by: the user who is deleting the workflow status
    :param workflow_status: the workflow status to delete
    :param target_status_id: the workflow status's id to which move the stories from the status being deleted
        - if not received, all the workflow status and its contained stories will be deleted
        - if received, the workflow status will be deleted but its contained stories won't (they will be first moved to
         the specified status)
    :return: bool
    """
    # before deleting the workflow status, its stories may be transferred to an existing workflow status
    # in the same workflow
    target_status = None
    if target_status_id:
        try:
            target_status = await get_workflow_status(
                status_id=target_status_id,
            )
        except WorkflowStatus.DoesNotExist as e:
            raise ex.NonExistingMoveToStatus(
                f"The status '{target_status_id}' doesn't exist"
            ) from e
        if target_status.id == workflow_status.id:
            raise ex.SameMoveToStatus(
                "The to-be-deleted status and the target-status cannot be the same"
            )

        stories_to_move = [
            story_ref
            async for story_ref in (
                stories_repositories.list_stories_qs(
                    filters={
                        "status_id": workflow_status.id,
                    },
                    order_by=["order"],
                ).values_list("ref", flat=True)
            )
        ]

        if stories_to_move:
            await stories_services.reorder_stories(
                reordered_by=deleted_by,
                project=workflow_status.project,
                workflow=workflow_status.workflow,
                target_status_id=target_status_id,
                stories_refs=stories_to_move,
            )

    deleted = await workflows_repositories.delete_workflow_status(
        status_id=workflow_status.id
    )
    if deleted > 0:
        await transaction_on_commit_async(
            workflows_events.emit_event_when_workflow_status_is_deleted
        )(
            project=workflow_status.project,
            workflow_status=workflow_status,
            target_status=target_status,
        )
        return True

    return False
