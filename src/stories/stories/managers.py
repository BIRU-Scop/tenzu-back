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

from uuid import UUID

from django.db import models
from django.db.models import Prefetch

from users.models import User


class StoryQuerySet(models.QuerySet):
    """ """

    def list_stories(self):
        return self.select_related("created_by").prefetch_related(
            Prefetch(
                "assignees",
                queryset=User.objects.all().order_by("-story_assignments__created_at"),
            )
        )


class StoryManager(models.Manager):
    def get_queryset(self) -> StoryQuerySet:
        return StoryQuerySet(self.model, using=self._db)

    def list_stories(
        self,
        project_id: UUID,
        workflow_slug: str,
        offset: int | None = None,
        limit: int | None = None,
        order_by: list | None = None,
    ):
        if order_by is None:
            order_by = ["order"]
        qs = (
            self.get_queryset()
            .list_stories()
            .filter(project_id=project_id, workflow__slug=workflow_slug)
            .order_by(*order_by)
        )
        if limit is not None and offset is not None:
            limit += offset

        return list(qs[offset:limit])
