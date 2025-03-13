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

from typing import List
from uuid import UUID

from pydantic import Field, StringConstraints, field_validator
from pydantic_core.core_schema import ValidationInfo
from typing_extensions import Annotated

from base.utils.uuid import decode_b64str_to_uuid
from base.validators import B64UUID, BaseModel
from commons.colors import NUM_COLORS
from commons.exceptions import api as ex

WorkflowStatusName = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=30)
]
WorkflowName = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=250)
]
WorkflowSlug = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=250)
]


class CreateWorkflowValidator(BaseModel):
    name: WorkflowName


class DeleteWorkflowQuery(BaseModel):
    move_to: WorkflowSlug | None = None


class CreateWorkflowStatusValidator(BaseModel):
    name: WorkflowStatusName
    color: Annotated[int, Field(gt=0, le=NUM_COLORS)]  # type: ignore


class UpdateWorkflowValidator(BaseModel):
    name: WorkflowName


class UpdateWorkflowStatusValidator(BaseModel):
    name: WorkflowStatusName | None


class ReorderValidator(BaseModel):
    place: str
    status: B64UUID

    @field_validator("place")
    @classmethod
    def check_valid_place(cls, v: str, info: ValidationInfo) -> str:
        assert v in ["before", "after"], "Place should be 'after' or 'before'"
        return v


class ReorderWorkflowStatusesValidator(BaseModel):
    statuses: Annotated[List[B64UUID], Field(min_length=1)]  # type: ignore[valid-type]
    reorder: ReorderValidator

    @field_validator("statuses")
    @classmethod
    def return_unique_statuses(cls, v: list[str], info: ValidationInfo) -> list[str]:
        """
        If there are some statuses ids repeated, ignore them,
        but keep the original order. Example:
        v = ["1", "1", "2", "1", "2"]
        return ["1", "2"]
        """
        return sorted(set(v), key=v.index)


class DeleteWorkflowStatusQuery(BaseModel):
    # TODO: fix to avoid double validation errors when using the B64UUID type (instead of str)
    move_to: str | None = None

    @field_validator("move_to")
    @classmethod
    def check_b64uuid_from_str(cls, v: str | None, info: ValidationInfo) -> UUID | None:
        if v is None:
            return None

        try:
            return decode_b64str_to_uuid(v)
        except ValueError:
            raise ex.ValidationError("Invalid 'move_to' workflow status")
