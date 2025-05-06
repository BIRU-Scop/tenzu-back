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

from asgiref.sync import sync_to_async

from .base import Factory, factory


class WorkflowFactory(Factory):
    name = factory.Sequence(lambda n: f"Workflow {n}")
    slug = factory.Sequence(lambda n: f"workflow-{n}")
    order = factory.Sequence(lambda n: n)
    project = factory.SubFactory("tests.utils.factories.ProjectFactory")

    @factory.post_generation
    def statuses(self, create, extracted, **kwargs):
        if extracted is None:
            return
        if not create:
            self._prefetched_objects_cache = {"statuses": extracted}
            for status in extracted:
                status.workflow = self
        elif isinstance(extracted, int):
            # hack to fill prefetch cache so that no db query will be needed to fetch statuses
            self._prefetched_objects_cache = {
                "statuses": [
                    WorkflowStatusFactory.create(workflow=self)
                    for _ in range(extracted)
                ]
            }

    class Meta:
        model = "workflows.Workflow"


class WorkflowStatusFactory(Factory):
    name = factory.Sequence(lambda n: f"Workflow Status {n}")
    color = factory.Faker("pyint", min_value=1, max_value=8)
    order = factory.Sequence(lambda n: n)
    workflow = factory.SubFactory("tests.utils.factories.WorkflowFactory", statuses=[])

    class Meta:
        model = "workflows.WorkflowStatus"


def build_workflow(**kwargs):
    return WorkflowFactory.build(**kwargs)


@sync_to_async
def create_workflow(**kwargs):
    return WorkflowFactory.create(**kwargs)


def build_workflow_status(**kwargs):
    return WorkflowStatusFactory.build(**kwargs)


@sync_to_async
def create_workflow_status(**kwargs):
    return WorkflowStatusFactory.create(**kwargs)
