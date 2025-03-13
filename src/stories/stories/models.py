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

from attachments.mixins import RelatedAttachmentsMixin
from base.db.mixins import (
    CreatedMetaInfoMixin,
    DescriptionUpdatedMetaInfoMixin,
    TitleUpdatedMetaInfoMixin,
)
from base.db.models import BaseModel
from base.occ.models import VersionedMixin
from comments.mixins import RelatedCommentsMixin
from commons.ordering import OrderedMixin
from mediafiles.mixins import RelatedMediafilesMixin
from projects.references.mixins import ProjectReferenceMixin


class Story(
    BaseModel,
    ProjectReferenceMixin,
    VersionedMixin,
    OrderedMixin,
    CreatedMetaInfoMixin,
    TitleUpdatedMetaInfoMixin,
    DescriptionUpdatedMetaInfoMixin,
    RelatedAttachmentsMixin,
    RelatedCommentsMixin,
    RelatedMediafilesMixin,
):
    title = models.CharField(
        max_length=500, null=False, blank=False, verbose_name="title"
    )
    description = models.TextField(null=True, blank=True, verbose_name="description")
    project = models.ForeignKey(
        "projects.Project",
        null=False,
        blank=False,
        related_name="stories",
        on_delete=models.CASCADE,
        verbose_name="project",
    )
    workflow = models.ForeignKey(
        "workflows.Workflow",
        null=False,
        blank=False,
        related_name="stories",
        on_delete=models.CASCADE,
        verbose_name="workflow",
    )
    status = models.ForeignKey(
        "workflows.WorkflowStatus",
        null=False,
        blank=False,
        related_name="stories",
        on_delete=models.CASCADE,
        verbose_name="status",
    )
    assignees = models.ManyToManyField(
        "users.User",
        related_name="stories",
        through="stories_assignments.StoryAssignment",
        through_fields=("story", "user"),
        verbose_name="assignees",
    )

    class Meta:
        verbose_name = "story"
        verbose_name_plural = "stories"
        constraints = ProjectReferenceMixin.Meta.constraints
        indexes = ProjectReferenceMixin.Meta.indexes
        ordering = ["project", "workflow", "order"]

    def __str__(self) -> str:
        return f"#{self.ref} {self.title}"

    def __repr__(self) -> str:
        return f"<Story #{self.ref}>"
