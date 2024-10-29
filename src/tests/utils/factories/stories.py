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

####################################################
# Story
####################################################


class StoryFactory(Factory):
    title = factory.Sequence(lambda n: f"Story {n}")
    description = factory.Sequence(lambda n: f"Description {n}")
    project = factory.SubFactory("tests.utils.factories.ProjectFactory")
    workflow = factory.SubFactory("tests.utils.factories.WorkflowFactory")
    status = factory.SubFactory("tests.utils.factories.WorkflowStatusFactory")
    created_by = factory.SubFactory("tests.utils.factories.UserFactory")
    order = factory.Sequence(lambda n: n + 1)

    class Meta:
        model = "stories.Story"


@sync_to_async
def create_story(**kwargs):
    return StoryFactory.create(**kwargs)


def build_story(**kwargs):
    return StoryFactory.build(**kwargs)


####################################################
# StoryAssignment
####################################################


class StoryAssignmentFactory(Factory):
    story = factory.SubFactory("tests.utils.factories.StoryFactory")
    user = factory.SubFactory("tests.utils.factories.UserFactory")

    class Meta:
        model = "stories_assignments.StoryAssignment"


@sync_to_async
def create_story_assignment(**kwargs):
    return StoryAssignmentFactory.create(**kwargs)


def build_story_assignment(**kwargs):
    return StoryAssignmentFactory.build(**kwargs)
