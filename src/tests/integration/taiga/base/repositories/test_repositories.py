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

from unittest.async_case import IsolatedAsyncioTestCase

import pytest

from base.repositories import neighbors as neighbors_repositories
from stories.stories.models import Story
from tests.utils import factories as f

pytestmark = pytest.mark.django_db(transaction=True)

##########################################################
# get_neighbors_sync
##########################################################


class GetObjectNeighbors(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.pj_admin = await f.create_user()
        self.project = await f.create_project(created_by=self.pj_admin)
        self.workflow_1 = await f.create_workflow(project=self.project)
        self.status_11 = await self.workflow_1.statuses.afirst()
        self.status_12 = await self.workflow_1.statuses.alast()

        self.story_111 = await f.create_story(project=self.project, workflow=self.workflow_1, status=self.status_11)
        self.story_112 = await f.create_story(project=self.project, workflow=self.workflow_1, status=self.status_12)

        self.workflow_2 = await f.create_workflow(project=self.project)
        self.status_21 = await self.workflow_2.statuses.afirst()
        self.story_221 = await f.create_story(project=self.project, workflow=self.workflow_2, status=self.status_21)

    async def test_get_neighbors_no_filter_no_prev_neighbor(self) -> None:
        neighbors = await neighbors_repositories.get_neighbors(obj=self.story_111)
        assert neighbors.prev is None
        assert neighbors.next == self.story_112

    async def test_get_neighbors_no_filter_no_next_neighbor_ok(self) -> None:
        neighbors = await neighbors_repositories.get_neighbors(obj=self.story_221)
        assert neighbors.prev == self.story_112
        assert neighbors.next is None

    async def test_get_neighbors_no_filter_both_neighbors(self) -> None:
        neighbors = await neighbors_repositories.get_neighbors(obj=self.story_112)
        assert neighbors.prev == self.story_111
        assert neighbors.next == self.story_221

    async def test_get_neighbors_with_model_queryset_broad_filters_all_match(
        self,
    ) -> None:
        same_story112_project_qs = Story.objects.filter(project_id=self.story_112.project.id).order_by(
            "status", "order"
        )

        neighbors = await neighbors_repositories.get_neighbors(
            obj=self.story_112, model_queryset=same_story112_project_qs
        )
        self.assertEqual(neighbors.prev, self.story_111)
        self.assertEqual(neighbors.next, self.story_221)

    async def test_get_neighbors_with_model_queryset_narrow_filters(self) -> None:
        same_story112_workflow_qs = Story.objects.filter(
            project_id=self.story_112.project.id, workflow_id=self.story_112.workflow.id
        ).order_by("status", "order")

        neighbors = await neighbors_repositories.get_neighbors(
            obj=self.story_112, model_queryset=same_story112_workflow_qs
        )
        assert neighbors.prev == self.story_111
        assert neighbors.next is None

    async def test_get_neighbors_with_model_queryset_filters_no_one_matches(
        self,
    ) -> None:
        same_story112_status_qs = Story.objects.filter(
            project_id=self.story_112.project.id,
            workflow_id=self.story_112.workflow.id,
            status_id=self.story_112.status.id,
        ).order_by("status", "order")

        neighbors = await neighbors_repositories.get_neighbors(
            obj=self.story_112, model_queryset=same_story112_status_qs
        )
        assert neighbors.prev is None
        assert neighbors.next is None
