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

from typing import Annotated, TypedDict

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import F, Q
from django.db.models.functions import Lower
from django_stubs_ext import Annotations

from base.db.models import BaseDBModel
from base.db.models.mixins import CreatedAtMetaInfoMixin
from commons.colors import NUM_COLORS

UNIQUE_LABEL_CONSTRAINT = "stories_tags_storytag_unique_project_lower_label"


class StoryTag(BaseDBModel):
    label = models.CharField(
        max_length=50, null=False, blank=False, verbose_name="label"
    )
    color = models.IntegerField(
        null=False,
        blank=False,
        verbose_name="color",
        validators=[MinValueValidator(1), MaxValueValidator(NUM_COLORS)],
    )
    project = models.ForeignKey(
        "projects.Project",
        null=False,
        blank=False,
        related_name="story_tags",
        on_delete=models.CASCADE,
        verbose_name="project",
    )

    class Meta:
        verbose_name = "story tag"
        verbose_name_plural = "story tags"
        constraints = [
            models.UniqueConstraint(
                Lower("label"),
                F("project"),
                name=UNIQUE_LABEL_CONSTRAINT,
            ),
            models.CheckConstraint(
                condition=Q(color__gte=1) & Q(color__lte=NUM_COLORS),
                name="%(app_label)s_%(class)s_color_between_1_and_num_colors",
            ),
        ]
        ordering = ["project", Lower("label")]

    def __str__(self) -> str:
        return self.label

    def __repr__(self) -> str:
        return f"<StoryTag {self.label}>"


class StoriesCountAnnotation(TypedDict):
    stories_count: int


StoryTagWithCount = Annotated[StoryTag, Annotations[StoriesCountAnnotation]]


class StoryTagAssignment(BaseDBModel, CreatedAtMetaInfoMixin):
    tag = models.ForeignKey(
        "stories_tags.StoryTag",
        null=False,
        blank=False,
        related_name="story_tag_assignments",
        on_delete=models.CASCADE,
        verbose_name="tag",
    )
    story = models.ForeignKey(
        "stories.Story",
        null=False,
        blank=False,
        related_name="story_tag_assignments",
        on_delete=models.CASCADE,
        verbose_name="story",
    )

    class Meta:
        verbose_name = "story tag assignment"
        verbose_name_plural = "story tag assignments"
        constraints = [
            models.UniqueConstraint(
                fields=["story", "tag"],
                name="%(app_label)s_%(class)s_unique_story_tag",
            ),
        ]
        indexes = [
            models.Index(fields=["story", "tag"]),
        ]
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"Tag {self.tag.label} assigned to story #{self.story.ref}"

    def __repr__(self) -> str:
        return f"<StoryTagAssignment Story #{self.story.ref} Tag: {self.tag.label}>"
