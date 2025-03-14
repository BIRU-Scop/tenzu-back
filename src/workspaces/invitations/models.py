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

from base.db import models
from base.db.mixins import CreatedAtMetaInfoMixin
from workspaces.invitations.choices import WorkspaceInvitationStatus


class WorkspaceInvitation(models.BaseModel, CreatedAtMetaInfoMixin):
    workspace = models.ForeignKey(
        "workspaces.Workspace",
        null=False,
        blank=False,
        related_name="invitations",
        on_delete=models.CASCADE,
        verbose_name="workspace",
    )
    user = models.ForeignKey(
        "users.User",
        null=True,
        blank=True,
        default=None,
        related_name="workspace_invitations",
        on_delete=models.CASCADE,
        verbose_name="user",
    )
    email = models.LowerEmailField(
        max_length=255, null=False, blank=False, verbose_name="email"
    )
    status = models.CharField(
        max_length=50,
        null=False,
        blank=False,
        choices=WorkspaceInvitationStatus.choices,
        default=WorkspaceInvitationStatus.PENDING,
        verbose_name="status",
    )
    invited_by = models.ForeignKey(
        "users.User",
        related_name="ihaveinvited+",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name="invited by",
    )
    num_emails_sent = models.IntegerField(
        default=1, null=False, blank=False, verbose_name="num emails sent"
    )
    resent_at = models.DateTimeField(null=True, blank=True, verbose_name="resent at")
    resent_by = models.ForeignKey(
        "users.User",
        related_name="ihaveresent+",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    revoked_by = models.ForeignKey(
        "users.User",
        related_name="ihaverevoked+",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    revoked_at = models.DateTimeField(null=True, blank=True, verbose_name="revoked at")

    class Meta:
        verbose_name = "workspace invitation"
        verbose_name_plural = "workspace invitations"
        constraints = [
            models.UniqueConstraint(
                fields=["workspace", "email"],
                name="%(app_label)s_%(class)s_unique_workspace_email",
            )
        ]
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["workspace", "email"]),
            models.Index(fields=["workspace", "user"]),
        ]
        ordering = ["workspace", "user", "email"]

    def __str__(self) -> str:
        return f"{self.workspace} - {self.email}"

    def __repr__(self) -> str:
        return f"<WorkspaceInvitation {self.workspace} {self.email}>"
