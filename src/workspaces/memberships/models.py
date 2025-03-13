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


class WorkspaceMembership(BaseModel, CreatedAtMetaInfoMixin):
    user = models.ForeignKey(
        "users.User",
        null=False,
        blank=False,
        related_name="workspace_memberships",
        on_delete=models.CASCADE,
        verbose_name="user",
    )
    workspace = models.ForeignKey(
        "workspaces.Workspace",
        null=False,
        blank=False,
        related_name="memberships",
        on_delete=models.CASCADE,
        verbose_name="workspace",
    )

    class Meta:
        verbose_name = "workspace membership"
        verbose_name_plural = "workspace memberships"
        constraints = [
            models.UniqueConstraint(
                fields=["workspace", "user"],
                name="%(app_label)s_%(class)s_unique_workspace_user",
            ),
        ]
        indexes = [
            models.Index(fields=["workspace", "user"]),
        ]
        ordering = ["workspace", "user"]

    def __str__(self) -> str:
        return f"{self.workspace} - {self.user}"

    def __repr__(self) -> str:
        return f"<WorkspaceMembership {self.workspace} {self.user}>"
