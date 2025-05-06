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
from typing import Any, cast
from uuid import UUID

from django.db.models import QuerySet

from base.repositories.neighbors import Neighbor
from base.utils.datetime import aware_utcnow
from commons.ordering import DEFAULT_ORDER_OFFSET, calculate_offset
from projects.projects.models import Project
from stories.stories import events as stories_events
from stories.stories import notifications as stories_notifications
from stories.stories import repositories as stories_repositories
from stories.stories.models import Story
from stories.stories.repositories import ASSIGNEE_IDS_ANNOTATION
from stories.stories.serializers import (
    ReorderStoriesSerializer,
    StoryDetailSerializer,
    StorySummarySerializer,
)
from stories.stories.services import exceptions as ex
from users.models import User
from workflows import repositories as workflows_repositories
from workflows.models import Workflow, WorkflowStatus

##########################################################
# create story
##########################################################


async def create_story(
    project: Project,
    workflow: Workflow,
    status_id: UUID,
    user: User,
    title: str,
    description: str | None,
) -> StoryDetailSerializer:
    # Validate data
    try:
        workflow_status = await workflows_repositories.get_workflow_status(
            status_id=status_id, filters={"workflow_id": workflow.id}
        )
    except WorkflowStatus.DoesNotExist as e:
        raise ex.InvalidStatusError("The provided status is not valid.") from e

    latest_story_order = await get_latest_story_order(workflow_status.id)
    order = DEFAULT_ORDER_OFFSET + (latest_story_order if latest_story_order else 0)

    # Create story
    story = await stories_repositories.create_story(
        title=title,
        description=description,
        project_id=project.id,
        workflow_id=workflow.id,
        status_id=workflow_status.id,
        user_id=user.id,
        order=order,
    )

    # Get detailed story
    detailed_story = await get_story_detail(project_id=project.id, ref=story.ref)

    # Emit event
    await stories_events.emit_event_when_story_is_created(
        project=project, story=detailed_story
    )

    return detailed_story


##########################################################
# list stories
##########################################################


async def list_stories(
    project_id: UUID,
    workflow_slug: str,
    offset: int | None = None,
    limit: int | None = None,
    order_by: list | None = None,
    get_assignees=True,
) -> list[StorySummarySerializer]:
    if order_by is None:
        order_by = ["order"]
    keys = ["ref", "title", "workflow_id", "project_id", "status_id", "version"]
    annotations = {"assignee_ids": ASSIGNEE_IDS_ANNOTATION} if get_assignees else {}
    qs: QuerySet[dict] = stories_repositories.list_stories_qs(
        filters={"project_id": project_id, "workflow__slug": workflow_slug},
        offset=offset,
        limit=limit,
        order_by=order_by,
    ).values(*keys, **annotations)

    return [
        StorySummarySerializer(
            **{key: value for key, value in story_dict.items()},
        )
        async for story_dict in qs
    ]


##########################################################
# get story
##########################################################


async def get_story(project_id: UUID, ref: int) -> Story:
    return await stories_repositories.get_story(
        ref=ref,
        filters={"project_id": project_id},
        select_related=["project", "project__workspace", "workflow", "created_by"],
    )


async def get_story_detail(
    project_id: UUID, ref: int, neighbors: Neighbor[Story] | None = None
) -> StoryDetailSerializer:
    story = await stories_repositories.get_story(
        ref=ref,
        filters={"project_id": project_id},
        select_related=[
            "created_by",
            "project",
            "workflow",
            "status",
            "project__workspace",
            "title_updated_by",
            "description_updated_by",
        ],
        get_assignees=True,
    )

    if not neighbors:
        neighbors = await stories_repositories.list_story_neighbors(
            story=story, filters={"workflow_id": story.workflow_id}
        )

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
        assignee_ids=story.assignee_ids,
        prev=neighbors.prev,
        next=neighbors.next,
        title_updated_by=story.title_updated_by,
        title_updated_at=story.title_updated_at,
        description_updated_by=story.description_updated_by,
        description_updated_at=story.description_updated_at,
    )


async def get_latest_story_order(status_id: UUID) -> int:
    return (
        await stories_repositories.list_stories_qs(
            filters={"status_id": status_id}, order_by=["-order"]
        )
        .values_list("order", flat=True)
        .afirst()
    )


##########################################################
# update stories
##########################################################


async def update_story(
    story: Story,
    current_version: int,
    updated_by: User,
    values: dict[str, Any] = {},
) -> StoryDetailSerializer:
    # Values to update
    update_values = await _validate_and_process_values_to_update(
        story=story, updated_by=updated_by, values=values
    )

    # Old neighbors
    old_neighbors = None
    if update_values.get("workflow", None):
        old_neighbors = await stories_repositories.list_story_neighbors(
            story=story, filters={"workflow_id": story.workflow_id}
        )

    # Update story
    if not await stories_repositories.update_story(
        id=story.id,
        current_version=current_version,
        values=update_values,
    ):
        raise ex.UpdatingStoryWithWrongVersionError(
            "Updating a story with the wrong version."
        )

    # Get detailed story
    detailed_story = await get_story_detail(
        project_id=story.project_id, ref=story.ref, neighbors=old_neighbors
    )

    # Emit event
    await stories_events.emit_event_when_story_is_updated(
        project=story.project,
        story=detailed_story,
        updates_attrs=[*update_values],
    )

    # Emit notifications
    if "workflow" in update_values:
        await stories_notifications.notify_when_story_workflow_change(
            story=story,
            workflow=update_values["workflow"].name,
            status=update_values["status"].name,
            emitted_by=updated_by,
        )
    elif "status" in update_values:
        await stories_notifications.notify_when_story_status_change(
            story=story,
            status=update_values["status"].name,
            emitted_by=updated_by,
        )

    return detailed_story


async def _validate_and_process_values_to_update(
    story: Story, updated_by: User, values: dict[str, Any]
) -> dict[str, Any]:
    output = values.copy()
    if "title" in output:
        output.update(
            title_updated_by=updated_by,
            title_updated_at=aware_utcnow(),
        )

    if "description" in output:
        output.update(
            description_updated_by=updated_by,
            description_updated_at=aware_utcnow(),
        )

    workflow_slug = output.pop("workflow_slug", None)
    if status_id := output.pop("status_id", None):
        if workflow_slug:
            raise ex.InvalidStatusError("The provided status is not valid.")
        try:
            status = await workflows_repositories.get_workflow_status(
                status_id=status_id, filters={"workflow_id": story.workflow_id}
            )
        except WorkflowStatus.DoesNotExist as e:
            raise ex.InvalidStatusError("The provided status is not valid.") from e

        if status.id != story.status_id:
            output.update(
                status=status, order=await _calculate_next_order(status_id=status.id)
            )

    elif workflow_slug:
        try:
            workflow = await workflows_repositories.get_workflow(
                filters={"project_id": story.project_id, "slug": workflow_slug},
                prefetch_related=["statuses"],
            )
        except Workflow.DoesNotExist as e:
            raise ex.InvalidWorkflowError("The provided workflow is not valid.") from e

        if workflow.slug != story.workflow.slug:
            # Set first status
            first_status_list = await workflows_repositories.list_workflow_statuses(
                workflow_id=workflow.id,
                order_by=["order"],
                offset=0,
                limit=1,
            )

            if not first_status_list:
                raise ex.WorkflowHasNotStatusesError(
                    "The provided workflow hasn't any statuses."
                )
            else:
                first_status = first_status_list[0]

            output.update(
                workflow=workflow,
                status=first_status,
                order=await _calculate_next_order(status_id=first_status.id),
            )

    return output


##########################################################
# update reorder stories
##########################################################


async def _calculate_offset(
    total_stories_to_reorder: int,
    target_status: WorkflowStatus,
    reorder_place: str | None = None,
    reorder_reference_story: Story | None = None,
    reordered_stories_ref: list[int] = None,
) -> tuple[int, int]:
    total_slots = total_stories_to_reorder + 1

    if not reorder_reference_story:
        latest_story_order = await get_latest_story_order(target_status.id)

        if latest_story_order:
            pre_order = latest_story_order
        else:
            pre_order = 0
        post_order = pre_order + (DEFAULT_ORDER_OFFSET * total_slots)
        offset = (post_order - pre_order) // total_slots
        return offset, pre_order

    neighbors = await stories_repositories.list_story_neighbors(
        story=reorder_reference_story,
        filters={"status_id": reorder_reference_story.status_id},
        excludes={"ref__in": reordered_stories_ref},
    )
    return calculate_offset(
        reorder_reference_story, reorder_place, total_slots, neighbors
    )


async def reorder_stories(
    reordered_by: User,
    project: Project,
    workflow: Workflow,
    target_status_id: UUID,
    stories_refs: list[int],
    reorder: dict[str, Any] | None = None,
) -> ReorderStoriesSerializer:
    # check target_status exists
    try:
        target_status = await workflows_repositories.get_workflow_status(
            status_id=target_status_id,
            filters={
                "workflow__project_id": project.id,
                "workflow__slug": workflow.slug,
            },
        )
    except WorkflowStatus.DoesNotExist as e:
        raise ex.InvalidStatusError(
            f"Status {target_status_id} doesn't exist in this project"
        ) from e

    # check anchor story exists
    if reorder:
        if reorder["ref"] in stories_refs:
            raise ex.InvalidStoryRefError(
                f"Ref {reorder['ref']} should not be part of the stories to reorder"
            )

        try:
            reorder_reference_story = await stories_repositories.get_story(
                ref=reorder["ref"],
                filters={
                    "workflow_id": workflow.id,
                    "status_id": target_status.id,
                },
            )
        except Story.DoesNotExist as e:
            raise ex.InvalidStoryRefError(
                f"Ref {reorder['ref']} doesn't exist in this project"
            ) from e
        reorder_place = reorder["place"]
    else:
        reorder_reference_story = None
        reorder_place = None

    # check all stories "to reorder" exist
    stories_to_reorder = await stories_repositories.list_stories_to_reorder(
        ref__in=stories_refs, filters={"workflow_id": workflow.id}
    )
    if len(stories_to_reorder) < len(stories_refs):
        raise ex.InvalidStoryRefError("One or more refs don't exist in this project")

    # calculate offset
    offset, pre_order = await _calculate_offset(
        total_stories_to_reorder=len(stories_to_reorder),
        target_status=target_status,
        reorder_reference_story=reorder_reference_story,
        reorder_place=reorder_place,
        reordered_stories_ref=stories_refs,
    )
    if offset == 0:
        # There is not enough space left between the stories where stories_to_reorder need to be inserted
        # We need to move more stories, this should happen very infrequently thanks to the offset
        after_stories = stories_repositories.list_stories_qs(
            filters={
                "status_id": reorder_reference_story.status_id,
                "order__gt": pre_order,
            },
            excludes={"ref__in": stories_refs},
            order_by=["status", "order"],
        )
        total_slots = len(stories_to_reorder) + 1
        async for nearby_after_story in after_stories:
            if nearby_after_story.order - pre_order < total_slots:
                stories_to_reorder.append(nearby_after_story)
                total_slots += 1
            else:
                offset = (nearby_after_story.order - pre_order) // total_slots
                break
        else:
            offset = DEFAULT_ORDER_OFFSET

    # update stories
    stories_to_update = []
    stories_with_changed_status = []
    for i, story in enumerate(stories_to_reorder):
        if story.status_id != target_status.id:
            stories_with_changed_status.append(story)

        story.status = target_status
        story.order = pre_order + (offset * (i + 1))
        stories_to_update.append(story)

    # save stories
    await stories_repositories.bulk_update_stories(
        objs_to_update=stories_to_update, fields_to_update=["status", "order"]
    )

    reorder_story_serializer = ReorderStoriesSerializer(
        status_id=target_status.id,
        status=target_status,
        stories=stories_refs,
        reorder=reorder,
    )

    # event
    await stories_events.emit_when_stories_are_reordered(
        project=project, reorder=reorder_story_serializer
    )

    # notifications
    for story in stories_with_changed_status:
        await stories_notifications.notify_when_story_status_change(
            story=story,
            status=story.status.name,
            emitted_by=reordered_by,
        )

    return reorder_story_serializer


async def _calculate_next_order(status_id: UUID) -> int:
    latest_story_order = await get_latest_story_order(status_id)

    return DEFAULT_ORDER_OFFSET + (latest_story_order if latest_story_order else 0)


##########################################################
# delete story
##########################################################


async def delete_story(story: Story, deleted_by: User) -> bool:
    deleted = await stories_repositories.delete_story(story_id=story.id)
    if deleted > 0:
        await stories_events.emit_event_when_story_is_deleted(
            project=story.project, ref=story.ref, deleted_by=deleted_by
        )
        await stories_notifications.notify_when_story_is_deleted(
            story=story,
            emitted_by=deleted_by,
        )
        return True
    return False
