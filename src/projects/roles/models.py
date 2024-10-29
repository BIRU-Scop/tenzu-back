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

from base.db import models
from base.utils.datetime import timestamp_mics
from base.utils.slug import generate_incremental_int_suffix, slugify_uniquely_for_queryset
from permissions.choices import ProjectPermissions


class ProjectRole(models.BaseModel):
    name = models.CharField(max_length=200, null=False, blank=False, verbose_name="name")
    slug = models.LowerSlugField(max_length=250, null=False, blank=True, verbose_name="slug")
    permissions = models.ArrayField(
        models.TextField(null=False, blank=False, choices=ProjectPermissions.choices),
        null=False,
        blank=False,
        default=list,
        verbose_name="permissions",
    )
    order = models.BigIntegerField(default=timestamp_mics, null=False, blank=False, verbose_name="order")
    is_admin = models.BooleanField(null=False, blank=False, default=False, verbose_name="is_admin")
    project = models.ForeignKey(
        "projects.Project",
        null=False,
        blank=False,
        related_name="roles",
        on_delete=models.CASCADE,
        verbose_name="project",
    )

    class Meta:
        verbose_name = "project role"
        verbose_name_plural = "project roles"
        constraints = [
            models.UniqueConstraint(
                fields=["project", "slug"],
                name="%(app_label)s_%(class)s_unique_project_slug",
            ),
            models.UniqueConstraint(
                fields=["project", "name"],
                name="%(app_label)s_%(class)s_unique_project_name",
            ),
        ]
        indexes = [
            models.Index(fields=["project", "slug"]),
        ]
        ordering = ["project", "order", "name"]

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"<ProjectRole {self.project} {self.slug}>"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self.slug:
            self.slug = slugify_uniquely_for_queryset(
                value=self.name,
                queryset=self.project.roles.all(),
                generate_suffix=generate_incremental_int_suffix(),
                use_always_suffix=False,
            )

        super().save(*args, **kwargs)
