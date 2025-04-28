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

from django.db import models

from projects.references import get_new_project_reference_id


class ProjectReferenceMixin(models.Model):
    ref = models.BigIntegerField(
        db_index=True, null=False, blank=False, default=0, verbose_name="ref"
    )

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=["project", "ref"], name="projects_unique_refs"
            )
        ]
        indexes = [
            models.Index(fields=["project", "ref"]),
        ]

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self.ref:
            self.ref = get_new_project_reference_id(project_id=self.project_id)  # type: ignore[attr-defined]

        super().save(*args, **kwargs)
