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
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models

from base.db.models import BaseModel
from base.db.models.mixins import CreatedMetaInfoMixin

#######################################################################
# Base Notification
######################################################################


class Notification(BaseModel, CreatedMetaInfoMixin):
    type = models.CharField(
        max_length=500,
        null=False,
        blank=False,
        verbose_name="type",
    )
    owner = models.ForeignKey(
        "users.User",
        null=False,
        blank=False,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name="owner",
    )
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="read at",
    )
    content = models.JSONField(
        null=False,
        blank=False,
        default=dict,
        encoder=DjangoJSONEncoder,
        verbose_name="content",
    )

    class Meta:
        verbose_name = "notification"
        verbose_name_plural = "notifications"
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=[
                    "owner",
                ]
            ),
            models.Index(fields=["owner", "read_at"]),
        ]
