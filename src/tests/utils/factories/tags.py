# -*- coding: utf-8 -*-
# Copyright (C) 2026 BIRU
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


class StoryTagFactory(Factory):
    label = factory.Sequence(lambda n: f"Story Tag {n}")
    color = factory.Faker("pyint", min_value=1, max_value=8)
    project = factory.SubFactory("tests.utils.factories.ProjectFactory")

    @factory.post_generation
    def stories_count(obj, create, extracted, **kwargs):
        obj.stories_count = 0 if extracted is None else extracted

    class Meta:
        model = "stories_tags.StoryTag"


class StoryTagAssignmentFactory(Factory):
    tag = factory.SubFactory("tests.utils.factories.StoryTagFactory")
    story = factory.SubFactory("tests.utils.factories.StoryFactory")

    class Meta:
        model = "stories_tags.StoryTagAssignment"


@sync_to_async
def create_story_tag(**kwargs):
    return StoryTagFactory.create(**kwargs)


def build_story_tag(**kwargs):
    return StoryTagFactory.build(**kwargs)


@sync_to_async
def create_story_tag_assignment(**kwargs):
    return StoryTagAssignmentFactory.create(**kwargs)


def build_story_tag_assignment(**kwargs):
    return StoryTagAssignmentFactory.build(**kwargs)
