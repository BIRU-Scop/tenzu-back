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

import pytest
from asgiref.sync import sync_to_async

from stories.assignments.models import StoryAssignment
from stories.stories import repositories
from tests.utils import factories as f

pytestmark = pytest.mark.django_db


##########################################################
# create_story
##########################################################


async def test_create_story_ok() -> None:
    user = await f.create_user()
    project = await f.create_simple_project()
    workflow = await f.create_workflow(project=project)
    status = await f.create_workflow_status(workflow=workflow)

    story = await repositories.create_story(
        title="test_create_story_ok",
        description="description",
        project_id=project.id,
        workflow_id=workflow.id,
        status_id=status.id,
        user_id=user.id,
        order=100,
    )

    assert story.title == "test_create_story_ok"


##########################################################
# list_stories
##########################################################


async def test_list_stories(project_template) -> None:
    project = await f.create_project(project_template)
    workflow_1 = await sync_to_async(project.workflows.first)()
    status_1 = await sync_to_async(workflow_1.statuses.first)()
    workflow_2 = await f.create_workflow(project=project)
    status_2 = await sync_to_async(workflow_2.statuses.first)()

    await f.create_story(project=project, workflow=workflow_1, status=status_1)
    await f.create_story(project=project, workflow=workflow_1, status=status_1)
    await f.create_story(project=project, workflow=workflow_2, status=status_2)

    stories = [
        story
        async for story in repositories.list_stories_qs(
            filters={"project_id": project.id}, select_related=["status"]
        )
    ]
    assert len(stories) == 3
    assert stories[0].title and stories[0].ref and stories[0].status
    stories = [
        story
        async for story in repositories.list_stories_qs(
            filters={"workflow_id": workflow_1.id}
        )
    ]
    assert len(stories) == 2

    stories = [
        # will fail in async context with "SynchronousOnlyOperation" if prefetch did not work
        (story, list(story.assignees.all()))
        async for story in repositories.list_stories_qs(
            filters={"workflow_id": workflow_2.id},
            prefetch_related=[repositories.ASSIGNEES_PREFETCH],
        )
    ]
    assert len(stories) == 1


##########################################################
# get_story
##########################################################


async def test_get_story() -> None:
    story1 = await f.create_story()
    story = await repositories.get_story(
        ref=story1.ref,
        filters={
            "project_id": story1.project.id,
            "workflow_id": story1.workflow.id,
        },
    )
    assert story1.ref == story.ref
    assert story1.title == story.title
    assert story1.id == story.id


##########################################################
# update_story
##########################################################


async def test_update_story_success(project_template) -> None:
    project = await f.create_project(project_template)
    workflow = await project.workflows.afirst()
    status = await workflow.statuses.afirst()
    story = await f.create_story(project=project, workflow=workflow, status=status)

    assert await repositories.update_story(
        id=story.id,
        current_version=story.version,
        values={"title": "new title", "description": "new description"},
    )


async def test_update_story_error(project_template) -> None:
    project = await f.create_project(project_template)
    workflow = await project.workflows.afirst()
    status = await workflow.statuses.afirst()
    story = await f.create_story(project=project, workflow=workflow, status=status)

    assert not await repositories.update_story(
        id=story.id,
        current_version=story.version + 1,
        values={"title": "new title"},
    )


##########################################################
# delete stories
##########################################################


async def test_delete_stories() -> None:
    user = await f.create_user()
    story = await f.create_story()
    await f.create_story_assignment(user=user, story=story)
    assert (
        await sync_to_async(
            StoryAssignment.objects.filter(story_id=story.id, user_id=user.id).count
        )()
        == 1
    )
    deleted = await repositories.delete_story(story_id=story.id)
    assert deleted == 2  # deleted story and assignment
    assert (
        await sync_to_async(
            StoryAssignment.objects.filter(story_id=story.id, user_id=user.id).count
        )()
        == 0
    )


##########################################################
# misc - list_story_neighbors
##########################################################


async def test_list_story_neighbors(project_template) -> None:
    project = await f.create_project(project_template)

    # same status for all stories
    workflow1 = await sync_to_async(project.workflows.first)()
    status11 = await sync_to_async(workflow1.statuses.first)()
    status12 = await sync_to_async(workflow1.statuses.last)()
    story1 = await f.create_story(project=project, workflow=workflow1, status=status11)
    story2 = await f.create_story(project=project, workflow=workflow1, status=status11)
    story3 = await f.create_story(project=project, workflow=workflow1, status=status11)
    await f.create_story(project=project, workflow=workflow1, status=status12)

    neighbors = await repositories.list_story_neighbors(
        story=story1, filters={"status_id": status11.id}
    )
    assert neighbors.prev is None
    assert neighbors.next.ref == story2.ref

    neighbors = await repositories.list_story_neighbors(
        story=story2, filters={"status_id": status11.id}
    )
    assert neighbors.prev.ref == story1.ref
    assert neighbors.next.ref == story3.ref

    neighbors = await repositories.list_story_neighbors(
        story=story3, filters={"status_id": status11.id}
    )
    assert neighbors.prev.ref == story2.ref
    assert neighbors.next is None

    # different statuses
    workflow2 = await f.create_workflow(project=project)
    status21 = await f.create_workflow_status(
        workflow=workflow2, name="New", color=1, order=1
    )
    status22 = await f.create_workflow_status(
        workflow=workflow2, name="In progress", color=1, order=2
    )
    status23 = await f.create_workflow_status(
        workflow=workflow2, name="Done", color=1, order=3
    )
    story1 = await f.create_story(project=project, workflow=workflow2, status=status21)
    story2 = await f.create_story(project=project, workflow=workflow2, status=status22)
    story3 = await f.create_story(project=project, workflow=workflow2, status=status23)

    neighbors = await repositories.list_story_neighbors(
        story=story1, filters={"workflow_id": workflow2.id}
    )
    assert neighbors.prev is None
    assert neighbors.next.ref == story2.ref

    neighbors = await repositories.list_story_neighbors(
        story=story1, filters={"status_id": status21.id}
    )
    assert neighbors.prev is None
    assert neighbors.next is None

    neighbors = await repositories.list_story_neighbors(
        story=story2, filters={"workflow_id": workflow2.id}
    )
    assert neighbors.prev.ref == story1.ref
    assert neighbors.next.ref == story3.ref

    neighbors = await repositories.list_story_neighbors(
        story=story3, filters={"workflow_id": workflow2.id}
    )
    assert neighbors.prev.ref == story2.ref
    assert neighbors.next is None


##########################################################
# misc - list_stories_to_reorder
##########################################################


async def test_list_stories_to_reorder(project_template) -> None:
    project = await f.create_project(project_template)
    workflow = await sync_to_async(project.workflows.first)()
    status = await sync_to_async(workflow.statuses.first)()

    story1 = await f.create_story(project=project, workflow=workflow, status=status)
    story2 = await f.create_story(project=project, workflow=workflow, status=status)
    story3 = await f.create_story(project=project, workflow=workflow, status=status)

    stories = await repositories.list_stories_to_reorder(
        ref__in=[story1.ref, story2.ref, story3.ref],
        filters={
            "status_id": status.id,
        },
    )
    assert stories[0].ref == story1.ref
    assert stories[1].ref == story2.ref
    assert stories[2].ref == story3.ref

    stories = await repositories.list_stories_to_reorder(
        ref__in=[story1.ref, story3.ref, story2.ref],
        filters={
            "status_id": status.id,
        },
    )
    assert stories[0].ref == story1.ref
    assert stories[1].ref == story3.ref
    assert stories[2].ref == story2.ref

    stories = await repositories.list_stories_to_reorder(
        ref__in=[story3.ref, story1.ref, story2.ref],
        filters={
            "status_id": status.id,
        },
    )
    assert stories[0].ref == story3.ref
    assert stories[1].ref == story1.ref
    assert stories[2].ref == story2.ref


##########################################################
# misc - bulk_update_workflow_to_stories
##########################################################


async def test_bulk_update_workflow_to_stories(project_template) -> None:
    project = await f.create_project(project_template)
    old_workflow = await sync_to_async(project.workflows.first)()
    new_workflow = await sync_to_async(project.workflows.first)()
    status = await sync_to_async(old_workflow.statuses.first)()
    story1 = await f.create_story(project=project, workflow=old_workflow, status=status)
    story2 = await f.create_story(project=project, workflow=old_workflow, status=status)

    await repositories.bulk_update_workflow_to_stories(
        statuses_ids=[status.id],
        old_workflow_id=old_workflow.id,
        new_workflow_id=new_workflow.id,
    )
    stories = [
        story
        async for story in repositories.list_stories_qs(
            filters={"workflow_id": old_workflow}, select_related=["workflow"]
        )
    ]
    assert story1 in stories and story2 in stories
    assert stories[0].workflow == new_workflow
    assert stories[1].workflow == new_workflow
