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
from typing import Literal

from ninja import UploadedFile
from pydantic import AfterValidator, WithJsonSchema, field_validator
from typing_extensions import Annotated

from commons.storage.api.validators import TusMetadata
from commons.validators import BaseValidatorSchema
from import_export.models import ProjectImportationType


class ImportationFileField(UploadedFile):
    pass


class _ImportProjectValidator(BaseValidatorSchema):
    origin_type: ProjectImportationType
    filename: str
    filetype: Literal["application/json"]

    @field_validator("origin_type", mode="after")
    @classmethod
    def is_supported(cls, value: ProjectImportationType) -> ProjectImportationType:
        if value not in (ProjectImportationType.TAIGA,):
            raise ValueError(f"Importation of type {value} is not supported yet")
        return value


def _parse_import_validator(v: dict) -> _ImportProjectValidator:
    return _ImportProjectValidator(**v)


ImportProjectValidator = Annotated[
    TusMetadata,
    AfterValidator(_parse_import_validator),
    WithJsonSchema(
        {
            "type": "string",
            "example": "originType VEE=,filename Zm9vLmpzb24=,filetype YXBwbGljYXRpb24vanNvbg==",
        }
    ),
]
