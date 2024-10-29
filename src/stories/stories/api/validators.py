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

from typing import Any, List

from pydantic import Field, StringConstraints, field_validator, model_validator
from pydantic.types import PositiveInt
from typing_extensions import Annotated

from base.validators import B64UUID, BaseModel

Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]


# class Title(ConstrainedStr):
#     strip_whitespace = True
#     min_length = 1
#     max_length = 500


class StoryValidator(BaseModel):
    title: Title
    description: str | None = None
    status: B64UUID


class UpdateStoryValidator(BaseModel):
    version: PositiveInt
    title: Title | None = None
    description: str | None = None
    status: B64UUID | None = None
    workflow: str | None = None

    @model_validator(mode="before")
    @classmethod
    def status_or_workflow(cls, values: dict[Any, Any]) -> dict[Any, Any]:
        status = values.get("status")
        workflow = values.get("workflow")
        assert not (status and workflow), "It's not allowed to update both the status and workspace"
        return values


class ReorderValidator(BaseModel):
    place: str
    ref: int

    @field_validator("place")
    @classmethod
    def check_valid_place(cls, v: str) -> str:
        assert v in ["before", "after"], "Place should be 'after' or 'before'"
        return v


class ReorderStoriesValidator(BaseModel):
    status: B64UUID
    stories: Annotated[List[int], Field(min_length=1)]  # type: ignore[valid-type]
    reorder: ReorderValidator | None = None

    @field_validator("stories")
    @classmethod
    def return_unique_stories(cls, v: list[int]) -> list[int]:
        """
        If there are some stories references repeated, ignore them,
        but keep the original order. Example:
        v = [1, 1, 9, 1, 9, 6, 9, 7]
        return [1, 9, 6, 7]
        """
        return sorted(set(v), key=v.index)

    def get_reorder_dict(self) -> dict[str, Any]:
        return self.model_dump()["reorder"]
