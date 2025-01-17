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

import pytest
from asgiref.sync import sync_to_async

from stories.stories import repositories, services
from tests.utils import factories as f

pytestmark = pytest.mark.django_db


##########################################################
# reorder_stories
##########################################################


async def test_not_reorder_in_empty_status() -> None:
    project = await f.create_project()
    workflow = await sync_to_async(project.workflows.first)()
    status_1 = await sync_to_async(workflow.statuses.first)()
    status_2 = await sync_to_async(workflow.statuses.last)()

    story1 = await f.create_story(project=project, workflow=workflow, status=status_1)
    story2 = await f.create_story(project=project, workflow=workflow, status=status_1)
    story3 = await f.create_story(project=project, workflow=workflow, status=status_1)
    # Current state
    # | status_1 | status_2 |
    # | -------- | -------- |
    # | story1   |          |
    # | story2   |          |
    # | story3   |          |

    await services.reorder_stories(
        reordered_by=project.created_by,
        project=project,
        workflow=workflow,
        target_status_id=status_2.id,
        stories_refs=[story2.ref, story3.ref],
    )
    # Now should be
    # | status_1 | status_2 |
    # | -------- | -------- |
    # | story1   | story2   |
    # |          | story3   |
    stories = await sync_to_async(list)(
        repositories.list_stories(filters={"status_id": status_1.id})
    )
    assert stories[0].ref == story1.ref
    stories = await sync_to_async(list)(
        repositories.list_stories(filters={"status_id": status_2.id})
    )
    assert stories[0].ref == story2.ref
    assert stories[0].order == Decimal(100)
    assert stories[1].ref == story3.ref
    assert stories[1].order == Decimal(200)


async def test_not_reorder_in_populated_status() -> None:
    project = await f.create_project()
    workflow = await sync_to_async(project.workflows.first)()
    status_1 = await sync_to_async(workflow.statuses.first)()
    status_2 = await sync_to_async(workflow.statuses.last)()

    story1 = await f.create_story(project=project, workflow=workflow, status=status_1)
    story2 = await f.create_story(project=project, workflow=workflow, status=status_1)
    story3 = await f.create_story(project=project, workflow=workflow, status=status_2)
    # Current state
    # | status_1 | status_2 |
    # | -------- | -------- |
    # | story1   | story3   |
    # | story2   |          |

    await services.reorder_stories(
        reordered_by=project.created_by,
        project=project,
        workflow=workflow,
        target_status_id=status_2.id,
        stories_refs=[story2.ref],
    )
    # Now should be
    # | status_1 | status_2 |
    # | -------- | -------- |
    # | story1   | story3   |
    # |          | story2   |
    stories = await sync_to_async(list)(
        repositories.list_stories(filters={"status_id": status_1.id})
    )
    assert stories[0].ref == story1.ref
    stories = await sync_to_async(list)(
        repositories.list_stories(filters={"status_id": status_2.id})
    )
    assert stories[0].ref == story3.ref
    assert stories[1].ref == story2.ref
    assert stories[1].order == story3.order + 100


async def test_after_in_the_end() -> None:
    project = await f.create_project()
    workflow = await sync_to_async(project.workflows.first)()
    status_1 = await sync_to_async(workflow.statuses.first)()
    status_2 = await sync_to_async(workflow.statuses.last)()

    story1 = await f.create_story(project=project, workflow=workflow, status=status_1)
    story2 = await f.create_story(project=project, workflow=workflow, status=status_1)
    story3 = await f.create_story(project=project, workflow=workflow, status=status_2)
    # Current state
    # | status_1 | status_2 |
    # | -------- | -------- |
    # | story1   | story3   |
    # | story2   |          |

    await services.reorder_stories(
        reordered_by=project.created_by,
        project=project,
        workflow=workflow,
        target_status_id=status_2.id,
        stories_refs=[story2.ref],
        reorder={"place": "after", "ref": story3.ref},
    )
    # Now should be
    # | status_1 | status_2 |
    # | -------- | -------- |
    # | story1   | story3   |
    # |          | story2   |
    stories = await sync_to_async(list)(
        repositories.list_stories(filters={"status_id": status_1.id})
    )
    assert stories[0].ref == story1.ref
    stories = await sync_to_async(list)(
        repositories.list_stories(filters={"status_id": status_2.id})
    )
    assert stories[0].ref == story3.ref
    assert stories[1].ref == story2.ref
    assert stories[1].order == story3.order + 100


async def test_after_in_the_middle() -> None:
    project = await f.create_project()
    workflow = await sync_to_async(project.workflows.first)()
    status_1 = await sync_to_async(workflow.statuses.first)()
    status_2 = await sync_to_async(workflow.statuses.last)()

    story1 = await f.create_story(project=project, workflow=workflow, status=status_1)
    story2 = await f.create_story(project=project, workflow=workflow, status=status_2)
    story3 = await f.create_story(project=project, workflow=workflow, status=status_2)
    # Current state
    # | status_1 | status_2 |
    # | -------- | -------- |
    # | story1   | story2   |
    # |          | story3   |

    await services.reorder_stories(
        reordered_by=project.created_by,
        project=project,
        workflow=workflow,
        target_status_id=status_2.id,
        stories_refs=[story1.ref],
        reorder={"place": "after", "ref": story2.ref},
    )
    # Now should be
    # | status_1 | status_2 |
    # | -------- | -------- |
    # |          | story2   |
    # |          | story1   |
    # |          | story3   |
    stories = await sync_to_async(list)(
        repositories.list_stories(filters={"status_id": status_1.id})
    )
    assert len(stories) == 0
    stories = await sync_to_async(list)(
        repositories.list_stories(filters={"status_id": status_2.id})
    )
    assert stories[0].ref == story2.ref
    assert stories[1].ref == story1.ref
    assert stories[1].order == story2.order + ((story3.order - story2.order) / 2)
    assert stories[2].ref == story3.ref


async def test_before_in_the_beginning() -> None:
    project = await f.create_project()
    workflow = await sync_to_async(project.workflows.first)()
    status_1 = await sync_to_async(workflow.statuses.first)()
    status_2 = await sync_to_async(workflow.statuses.last)()

    story1 = await f.create_story(project=project, workflow=workflow, status=status_1)
    story2 = await f.create_story(project=project, workflow=workflow, status=status_2)
    story3 = await f.create_story(project=project, workflow=workflow, status=status_2)
    # Current state
    # | status_1 | status_2 |
    # | -------- | -------- |
    # | story1   | story2   |
    # |          | story3   |

    await services.reorder_stories(
        reordered_by=project.created_by,
        project=project,
        workflow=workflow,
        target_status_id=status_2.id,
        stories_refs=[story1.ref],
        reorder={"place": "before", "ref": story2.ref},
    )
    # Now should be
    # | status_1 | status_2 |
    # | -------- | -------- |
    # |          | story1   |
    # |          | story2   |
    # |          | story3   |
    stories = await sync_to_async(list)(
        repositories.list_stories(filters={"status_id": status_1.id})
    )
    assert len(stories) == 0
    stories = await sync_to_async(list)(
        repositories.list_stories(filters={"status_id": status_2.id})
    )
    assert stories[0].ref == story1.ref
    assert stories[0].order == story2.order / 2
    assert stories[1].ref == story2.ref
    assert stories[2].ref == story3.ref


async def test_before_in_the_middle() -> None:
    project = await f.create_project()
    workflow = await sync_to_async(project.workflows.first)()
    status_1 = await sync_to_async(workflow.statuses.first)()
    status_2 = await sync_to_async(workflow.statuses.last)()

    story1 = await f.create_story(project=project, workflow=workflow, status=status_1)
    story2 = await f.create_story(project=project, workflow=workflow, status=status_2)
    story3 = await f.create_story(project=project, workflow=workflow, status=status_2)
    # Current state
    # | status_1 | status_2 |
    # | -------- | -------- |
    # | story1   | story2   |
    # |          | story3   |

    await services.reorder_stories(
        reordered_by=project.created_by,
        project=project,
        workflow=workflow,
        target_status_id=status_2.id,
        stories_refs=[story1.ref],
        reorder={"place": "before", "ref": story3.ref},
    )
    # Now should be
    # | status_1 | status_2 |
    # | -------- | -------- |
    # |          | story2   |
    # |          | story1   |
    # |          | story3   |
    stories = await sync_to_async(list)(
        repositories.list_stories(filters={"status_id": status_1.id})
    )
    assert len(stories) == 0
    stories = await sync_to_async(list)(
        repositories.list_stories(filters={"status_id": status_2.id})
    )
    assert stories[0].ref == story2.ref
    assert stories[1].ref == story1.ref
    assert stories[1].order == story2.order + ((story3.order - story2.order) / 2)
    assert stories[2].ref == story3.ref
