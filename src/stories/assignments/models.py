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

from django.db import models

from base.db.mixins import CreatedAtMetaInfoMixin
from base.db.models import BaseModel


class StoryAssignment(BaseModel, CreatedAtMetaInfoMixin):
    user = models.ForeignKey(
        "users.User",
        null=False,
        blank=False,
        related_name="story_assignments",
        on_delete=models.CASCADE,
        verbose_name="user",
    )
    story = models.ForeignKey(
        "stories.Story",
        null=False,
        blank=False,
        related_name="story_assignments",
        on_delete=models.CASCADE,
        verbose_name="story",
    )

    class Meta:
        verbose_name = "story assignment"
        verbose_name_plural = "story assignments"
        constraints = [
            models.UniqueConstraint(
                fields=["story", "user"],
                name="%(app_label)s_%(class)s_unique_story_user",
            ),
        ]
        indexes = [
            models.Index(fields=["story", "user"]),
        ]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"User {self.user.username} assigned to story #{self.story.ref}"

    def __repr__(self) -> str:
        return f"<StoryAssignment Story #{self.story.ref} User: {self.user.username}>"
