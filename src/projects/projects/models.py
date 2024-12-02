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

import functools
from typing import Any

from django.core.validators import MaxValueValidator
from slugify import slugify

from base.db import models
from base.db.mixins import CreatedMetaInfoMixin, ModifiedAtMetaInfoMixin
from base.utils.files import get_obfuscated_file_path
from base.utils.slug import slugify_uniquely
from commons.colors import NUM_COLORS
from permissions.choices import ProjectPermissions
from projects import references

get_project_logo_file_path = functools.partial(
    get_obfuscated_file_path, base_path="project"
)


class Project(models.BaseModel, CreatedMetaInfoMixin, ModifiedAtMetaInfoMixin):
    name = models.CharField(max_length=80, null=False, blank=False, verbose_name="name")
    description = models.CharField(
        max_length=220, null=False, blank=True, default="", verbose_name="description"
    )
    color = models.IntegerField(
        null=False,
        blank=True,
        default=1,
        verbose_name="color",
        validators=[MaxValueValidator(NUM_COLORS)],
    )
    logo = models.FileField(
        max_length=500,
        null=True,
        blank=True,
        upload_to=get_project_logo_file_path,
        verbose_name="logo",
    )

    workspace = models.ForeignKey(
        "workspaces.Workspace",
        null=False,
        blank=False,
        related_name="projects",
        on_delete=models.CASCADE,
        verbose_name="workspace",
    )

    members = models.ManyToManyField(
        "users.User",
        related_name="projects",
        through="projects_memberships.ProjectMembership",
        through_fields=("project", "user"),
        verbose_name="members",
    )

    public_permissions = models.ArrayField(
        models.TextField(null=False, blank=False, choices=ProjectPermissions.choices),
        null=False,
        blank=False,
        default=list,
        verbose_name="public permissions",
    )

    class Meta:
        verbose_name = "project"
        verbose_name_plural = "projects"
        indexes = [
            models.Index(fields=["workspace", "id"]),
        ]
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"<Project {self.name}>"

    @property
    def slug(self) -> str:
        return slugify(self.name)

    @property
    def public_user_can_view(self) -> bool:
        """
        Any registered user can view the project
        """
        return bool(self.public_permissions)

    @property
    def anon_user_can_view(self) -> bool:
        """
        Any unregistered/anonymous user can view the project
        """
        return bool(self.anon_permissions)

    @property
    def anon_permissions(self) -> list[str]:
        return list(
            filter(lambda x: x.startswith("view_"), self.public_permissions or [])
        )

    def save(self, *args: Any, **kwargs: Any) -> None:
        super().save(*args, **kwargs)

        references.create_project_references_sequence(project_id=self.id)


class ProjectTemplate(models.BaseModel):
    name = models.CharField(
        max_length=250, null=False, blank=False, verbose_name="name"
    )
    slug = models.LowerSlugField(
        max_length=250, null=False, blank=True, unique=True, verbose_name="slug"
    )
    roles = models.JSONField(null=True, blank=True, verbose_name="roles")
    workflows = models.JSONField(null=True, blank=True, verbose_name="workflows")
    workflow_statuses = models.JSONField(
        null=True, blank=True, verbose_name="workflow statuses"
    )

    class Meta:
        verbose_name = "project template"
        verbose_name_plural = "project templates"
        indexes = [
            models.Index(fields=["slug"]),
        ]
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"<Project Template: {self.name}>"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self.slug:
            self.slug = slugify_uniquely(value=self.name, model=self.__class__)
        super().save(*args, **kwargs)
