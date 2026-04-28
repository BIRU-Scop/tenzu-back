# -*- coding: utf-8 -*-
# Copyright (C) 2024-2026 BIRU
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
import json
from typing import Any

from django.core.files.uploadedfile import UploadedFile as DjangoUploadedFile
from ninja import UploadedFile
from pydantic import field_validator

from commons.validators import BaseModel
from import_export.models import ProjectImportationType


class ImportationFileField(UploadedFile):
    @classmethod
    def _validate(cls, v: Any, _: Any) -> Any:
        importation_file: DjangoUploadedFile = super()._validate(v, _)
        if importation_file:
            supported_content_type = {"application/json"}
            if importation_file.content_type not in supported_content_type:
                raise ValueError(
                    f"Invalid importation content type, expected one of {', '.join(supported_content_type)}"
                )
        return importation_file


class ImportProjectValidator(BaseModel):
    origin_type: ProjectImportationType

    @field_validator("origin_type", mode="after")
    @classmethod
    def is_supported(cls, value: ProjectImportationType) -> ProjectImportationType:
        if value not in (ProjectImportationType.TAIGA,):
            raise ValueError(f"Importation of type {value} is not supported yet")
        return value
