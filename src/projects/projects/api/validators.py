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

from typing import Optional

from ninja import UploadedFile
from pydantic import (
    AfterValidator,
    Field,
    PlainValidator,
    StringConstraints,
    WithJsonSchema,
    field_validator,
)
from pydantic_core.core_schema import ValidationInfo
from typing_extensions import Annotated, Literal

from base.utils.images import valid_content_type, valid_image_content
from base.utils.uuid import decode_b64str_to_uuid
from base.validators import BaseModel
from commons.colors import NUM_COLORS
from permissions.validators import Permissions

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


# Need to add the JsonSchema because of the PlainValidator
# (https://docs.pydantic.dev/latest/concepts/json_schema/#withjsonschema-annotation)
LogoField = Annotated[
    UploadedFile,
    PlainValidator(lambda x: validate_logo(x)),
    WithJsonSchema(dict(type="string", format="binary")),
]


class ProjectValidator(BaseModel):
    name: Annotated[str, StringConstraints(strip_whitespace=True, max_length=80)]  # type: ignore
    workspace_id: B64UUID
    # description max_length validation to 220 characteres to resolve
    # this problem https://stackoverflow.com/a/69851342/2883148
    description: Annotated[str, StringConstraints(max_length=220)] | None = None  # type: ignore
    color: Annotated[int, Field(gt=0, lte=NUM_COLORS)] | None = None  # type: ignore

    @field_validator("name")
    @classmethod
    def check_name_not_empty(cls, v: str, info: ValidationInfo) -> str:
        assert v != "", "Empty name is not allowed"
        return v


class UpdateProjectValidator(BaseModel):
    name: str | None
    description: str | None
    logo: LogoField | Literal[""] | None = None

    @field_validator("logo")
    @classmethod
    def logo_can_be_empty_str(cls, v: str) -> Optional[str]:
        if v:
            return v
        return None


class PermissionsValidator(BaseModel):
    permissions: Permissions
