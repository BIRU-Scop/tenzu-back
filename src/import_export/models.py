# Copyright (C) 2026 BIRU
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
from typing import TypedDict

from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models import JSONField, TextChoices
from pydantic import EmailStr

from base.db.models import BaseDBModel
from base.db.models.mixins import CreatedMetaInfoMixin, ModifiedAtMetaInfoMixin
from base.serializers import UUIDB64
from base.utils.files import get_obfuscated_file_path


class ProjectImportationType(TextChoices):
    TENZU = "TZ", "Tenzu"
    TAIGA = "TA", "Taiga"
    TRELLO = "TR", "Trello"


class ImportationStatus(models.TextChoices):
    PENDING = "P", "Pending"
    ONGOING = "O", "Ongoing"
    ACTION_NEEDED = "A", "Action needed"
    SUCCESS = "S", "Success"
    FAILURE = "F", "Failure"


class ImportationError(models.TextChoices):
    INVALID = "file_validation_failed"
    SERVER_ERROR = "server_error_while_processing"


get_importation_source_file_path = functools.partial(
    get_obfuscated_file_path, base_path="project/importation"
)


class ProjectImportationData(TypedDict, total=False):
    error_code: ImportationError
    progress_percentage: int


class ProjectImportationPendingInvitation(TypedDict, total=True):
    email: EmailStr
    role_id: UUIDB64
    assigned_stories_ids: list[UUIDB64]
    created_stories_ids: list[UUIDB64]
    created_attachments_ids: list[UUIDB64]
    created_comments_ids: list[UUIDB64]
    deleted_comments_ids: list[UUIDB64]


class ProjectImportation(BaseDBModel, CreatedMetaInfoMixin, ModifiedAtMetaInfoMixin):
    origin_type = models.CharField(
        max_length=2,
        null=False,
        blank=False,
        choices=ProjectImportationType.choices,
    )
    status = models.CharField(
        max_length=1,
        choices=ImportationStatus.choices,
        default=ImportationStatus.PENDING,
    )
    source = models.FileField(
        max_length=500,
        upload_to=get_importation_source_file_path,
    )
    pending_invites: list[ProjectImportationPendingInvitation] = JSONField(
        null=False,
        blank=True,
        default=list,
        encoder=DjangoJSONEncoder,
    )
    extra_data: ProjectImportationData = JSONField(
        null=False,
        blank=True,
        default=dict,
        encoder=DjangoJSONEncoder,
    )
    project = models.OneToOneField(
        "projects.Project",
        null=True,
        blank=True,
        related_name="importation",
        on_delete=models.CASCADE,
        verbose_name="project",
    )
    workspace = models.ForeignKey(
        "workspaces.Workspace",
        null=False,
        blank=False,
        related_name="project_importations",
        on_delete=models.CASCADE,
        verbose_name="workspace",
    )

    class Meta:
        ordering = ["-created_at"]
