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

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import base.db.models
import base.db.models.fields
import base.utils.datetime


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("workspaces", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="WorkspaceInvitation",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        blank=True,
                        default=base.db.models.uuid_generator,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        default=base.utils.datetime.aware_utcnow,
                        verbose_name="created at",
                    ),
                ),
                (
                    "email",
                    base.db.models.fields.LowerEmailField(
                        max_length=255, verbose_name="email"
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("accepted", "Accepted"),
                            ("revoked", "Revoked"),
                        ],
                        default="pending",
                        max_length=50,
                        verbose_name="status",
                    ),
                ),
                (
                    "num_emails_sent",
                    models.IntegerField(default=1, verbose_name="num emails sent"),
                ),
                (
                    "resent_at",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="resent at"
                    ),
                ),
                (
                    "revoked_at",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="revoked at"
                    ),
                ),
                (
                    "invited_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="ihaveinvited+",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="invited by",
                    ),
                ),
                (
                    "resent_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="ihaveresent+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "revoked_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="ihaverevoked+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        default=None,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="workspace_invitations",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="user",
                    ),
                ),
                (
                    "workspace",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="invitations",
                        to="workspaces.workspace",
                        verbose_name="workspace",
                    ),
                ),
            ],
            options={
                "verbose_name": "workspace invitation",
                "verbose_name_plural": "workspace invitations",
                "ordering": ["workspace", "user", "email"],
            },
        ),
        migrations.AddIndex(
            model_name="workspaceinvitation",
            index=models.Index(fields=["email"], name="workspaces__email_b0bc4c_idx"),
        ),
        migrations.AddIndex(
            model_name="workspaceinvitation",
            index=models.Index(
                fields=["workspace", "email"], name="workspaces__workspa_5b9964_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="workspaceinvitation",
            index=models.Index(
                fields=["workspace", "user"], name="workspaces__workspa_c70bed_idx"
            ),
        ),
        migrations.AddConstraint(
            model_name="workspaceinvitation",
            constraint=models.UniqueConstraint(
                fields=("workspace", "email"),
                name="workspaces_invitations_workspaceinvitation_unique_workspace_email",
            ),
        ),
    ]
