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
from typing import Any, Literal

from ninja import UploadedFile
from pydantic import (
    AfterValidator,
    BeforeValidator,
    Field,
    PlainValidator,
    StringConstraints,
    WithJsonSchema,
)
from typing_extensions import Annotated

from base.utils.images import valid_content_type, valid_image_content
from base.utils.uuid import decode_b64str_to_uuid
from commons.colors import NUM_COLORS
from commons.validators import BaseModel

B64UUID = Annotated[
    str,
    AfterValidator(lambda x: decode_b64str_to_uuid(x)),
    WithJsonSchema({"type": "str", "examples": "6JgsbGyoEe2VExhWgGrI2w"}),
]


def validate_logo(logo: UploadedFile):
    if logo:
        if not valid_content_type(logo):
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


class ProjectValidator(BaseModel):
    name: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)
    ]  # type: ignore
    workspace_id: B64UUID
    # description max_length validation to 220 characteres to resolve
    # this problem https://stackoverflow.com/a/69851342/2883148
    description: Annotated[str, StringConstraints(max_length=220)] | None = None  # type: ignore
    color: Annotated[int, Field(gt=0, le=NUM_COLORS)] | None = None  # type: ignore
    logo: LogoField | None = None


class UpdateProjectValidator(BaseModel):
    name: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)
    ] = None
    description: str = None
