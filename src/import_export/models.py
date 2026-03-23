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
from pathlib import Path

from django.db import models
from django.db.models import JSONField, TextChoices

from base.db.models import BaseModel
from base.db.models.mixins import CreatedMetaInfoMixin
from base.utils.files import get_obfuscated_file_path


class ImportationType(TextChoices):
    TAIGA = "TA", "Taiga"
    TRELLO = "TR", "Trello"


class ImportationStatus(models.TextChoices):
    PENDING = "P", "Pending"
    ONGOING = "O", "Ongoing"
    ACTION_NEEDED = "A", "Action needed"
    SUCCESS = "S", "Success"
    FAILURE = "F", "Failure"


get_importation_source_file_path = functools.partial(
    get_obfuscated_file_path, base_path="importation"
)


def get_error_result_file_path(
    instance: "Importation", filename: str, base_path: str = ""
) -> str:
    source_path = Path(instance.source.name)
    return str(source_path.with_suffix(f".error_result{''.join(source_path.suffixes)}"))


class Importation(BaseModel, CreatedMetaInfoMixin):
    origin_type = models.CharField(
        max_length=2,
        null=False,
        blank=False,
        choices=ImportationType.choices,
    )
    status = models.CharField(
        max_length=1,
        choices=ImportationStatus.choices,
        default=ImportationStatus.PENDING,
    )
    source = models.FileField(
        upload_to=get_importation_source_file_path,
    )
    error_result_file = models.FileField(
        null=True,
        blank=True,
        upload_to=get_error_result_file_path,
    )
    extra_data = JSONField(null=False, blank=True, default=dict)

    class Meta:
        ordering = ["-created_at"]
