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

from base.serializers import BaseSchema
from stories.tags.serializers import (
    StoryTagAssignmentSerializer,
    StoryTagWithCountSerializer,
)


class CreateStoryTagContent(BaseSchema):
    story_tag: StoryTagWithCountSerializer


class UpdateStoryTagContent(BaseSchema):
    story_tag: StoryTagWithCountSerializer


class DeleteStoryTagContent(BaseSchema):
    story_tag: StoryTagWithCountSerializer


class CreateStoryTagAssignmentContent(BaseSchema):
    story_tag_assignment: StoryTagAssignmentSerializer


class DeleteStoryTagAssignmentContent(BaseSchema):
    story_tag_assignment: StoryTagAssignmentSerializer
