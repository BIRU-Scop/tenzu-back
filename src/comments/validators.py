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

from typing import List, Literal

from pydantic import Field, model_serializer
from pydantic.alias_generators import to_snake

from base.api.ordering import OrderQuery
from commons.validators import BaseModel, StrNotEmpty

CommentOrderQuery = OrderQuery(
    allowed=[
        "created_at",
        "-created_at",
    ],
    default=[
        "-created_at",
    ],
)


class CommentOrderSortQuery(BaseModel):
    order: List[Literal["createdAt", "-createdAt"]] = Field(
        default_factory=lambda: ["-createdAt"]
    )

    @model_serializer(return_type=List[str])
    def flat_list_as_result(self):
        return [to_snake(data) for data in self.order]


class CreateCommentValidator(BaseModel):
    text: StrNotEmpty


class UpdateCommentValidator(BaseModel):
    text: StrNotEmpty
