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


class ProjectMembership(BaseModel, CreatedAtMetaInfoMixin):
    user = models.ForeignKey(
        "users.User",
        null=False,
        blank=False,
        related_name="project_memberships",
        on_delete=models.CASCADE,
        verbose_name="user",
    )
    project = models.ForeignKey(
        "projects.Project",
        null=False,
        blank=False,
        related_name="memberships",
        on_delete=models.CASCADE,
        verbose_name="project",
    )
    role = models.ForeignKey(
        "projects_roles.ProjectRole",
        null=False,
        blank=False,
        related_name="memberships",
        on_delete=models.CASCADE,
        verbose_name="role",
    )

    class Meta:
        verbose_name = "project membership"
        verbose_name_plural = "project memberships"
        constraints = [
            models.UniqueConstraint(
                fields=["project", "user"],
                name="%(app_label)s_%(class)s_unique_project_user",
            ),
        ]
        indexes = [
            models.Index(fields=["project", "user"]),
        ]
        ordering = ["project", "user"]

    def __str__(self) -> str:
        return f"{self.project} - {self.user}"

    def __repr__(self) -> str:
        return f"<ProjectMembership {self.project} {self.user}>"
