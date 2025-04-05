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
from django.core.validators import MaxValueValidator
from django.db import models
from django_stubs_ext.db.models.manager import ManyRelatedManager
from slugify import slugify

from base.db.mixins import CreatedMetaInfoMixin, ModifiedAtMetaInfoMixin
from base.db.models import BaseModel
from commons.colors import NUM_COLORS


class Workspace(BaseModel, CreatedMetaInfoMixin, ModifiedAtMetaInfoMixin):
    name = models.CharField(max_length=40, null=False, blank=False, verbose_name="name")
    color = models.IntegerField(
        null=False,
        blank=False,
        default=1,
        verbose_name="color",
        validators=[MaxValueValidator(NUM_COLORS)],
    )

    members = models.ManyToManyField(
        "users.User",
        related_name="workspaces",
        through="workspaces_memberships.WorkspaceMembership",
        through_fields=("workspace", "user"),
        verbose_name="members",
    )
    roles: ManyRelatedManager
    invitations: ManyRelatedManager

    class Meta:
        verbose_name = "workspace"
        verbose_name_plural = "workspaces"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"<Workspace {self.name}>"

    @property
    def slug(self) -> str:
        return slugify(self.name)
