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

from typing import Any

from django.core.validators import MaxValueValidator

from base.db import models
from base.utils.slug import (
    generate_incremental_int_suffix,
    slugify_uniquely_for_queryset,
)
from commons.colors import NUM_COLORS
from commons.ordering import OrderedMixin
from projects.projects.models import Project


class Workflow(models.BaseModel, OrderedMixin):
    name = models.CharField(
        max_length=250, null=False, blank=False, verbose_name="name"
    )
    slug = models.LowerSlugField(
        max_length=250, null=False, blank=False, verbose_name="slug"
    )
    project = models.ForeignKey(
        "projects.Project",
        null=False,
        blank=False,
        related_name="workflows",
        on_delete=models.CASCADE,
        verbose_name="project",
    )

    class Meta:
        verbose_name = "workflow"
        verbose_name_plural = "workflows"
        constraints = [
            models.UniqueConstraint(
                fields=["project", "slug"],
                name="%(app_label)s_%(class)s_unique_project_slug",
            ),
        ]
        indexes = [
            models.Index(fields=["project", "slug"]),
        ]
        ordering = ["project", "order", "name"]

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"<Workflow {self.name}>"

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.slug = slugify_uniquely_for_queryset(
            value=self.name,
            queryset=self.project.workflows.all(),
            generate_suffix=generate_incremental_int_suffix(),
            use_always_suffix=False,
        )

        super().save(*args, **kwargs)


class WorkflowStatus(models.BaseModel, OrderedMixin):
    name = models.CharField(max_length=30, null=False, blank=False, verbose_name="name")
    color = models.IntegerField(
        null=False,
        blank=False,
        default=1,
        verbose_name="color",
        validators=[MaxValueValidator(NUM_COLORS)],
    )
    workflow = models.ForeignKey(
        "workflows.Workflow",
        null=False,
        blank=False,
        related_name="statuses",
        on_delete=models.CASCADE,
        verbose_name="workflow",
    )

    class Meta:
        verbose_name = "workflow status"
        verbose_name_plural = "workflow statuses"
        constraints = [
            models.UniqueConstraint(
                fields=["workflow", "id"],
                name="%(app_label)s_%(class)s_unique_workflow_id",
            ),
        ]
        indexes = [
            models.Index(fields=["workflow", "id"]),
        ]
        ordering = ["workflow", "order", "name"]

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"<WorkflowStatus {self.name}>"

    @property
    def project(self) -> Project:
        return self.workflow.project
