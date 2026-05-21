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
from typing import Any, Literal

from ninja import UploadedFile
from pydantic import (
    BeforeValidator,
    PlainValidator,
    StringConstraints,
    conint,
    constr,
)
from typing_extensions import Annotated

from base.utils.images import valid_image_content, valid_image_content_type
from commons.colors import NUM_COLORS
from commons.validators import BaseModel


def validate_logo(logo: UploadedFile) -> UploadedFile:
    if logo:
        if not valid_image_content_type(logo):
            raise ValueError("Invalid image content type")
        if not valid_image_content(logo):
            raise ValueError("Invalid image content")
    return logo


def logo_can_be_empty_str(v: Any) -> Any | None:
    if v == "":
        return None
    return v


# Need to add the JsonSchema because of the PlainValidator
# (https://docs.pydantic.dev/latest/concepts/json_schema/#withjsonschema-annotation)
LogoField = Annotated[
    UploadedFile,
    BeforeValidator(
        logo_can_be_empty_str, json_schema_input_type=UploadedFile | Literal[""]
    ),
    PlainValidator(validate_logo, json_schema_input_type=UploadedFile),
]


class CreateProjectValidator(BaseModel):
    name: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)
    ]  # type: ignore
    description: constr(max_length=220) | None = None  # type: ignore
    color: conint(gt=0, le=NUM_COLORS) | None = None  # type: ignore


class UpdateProjectValidator(BaseModel):
    name: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)
    ] = None
    description: str = None
