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

from typing import Any

from pydantic import BaseModel, Field

from base.logging.context import get_current_correlation_id

EventContent = BaseModel | None


class Event(BaseModel):
    type: str
    content: dict[str, Any] | EventContent = None
    correlation_id: str | None = Field(default_factory=get_current_correlation_id)

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Event)
            and self.type == other.type
            and self.correlation_id == other.correlation_id
            and self.content == other.content
        )

    def __repr__(self) -> str:
        _content = self.content.dict(by_alias=True) if isinstance(self.content, BaseModel) else self.content
        return f"Event(type={self.type!r}, correlation_id={self.correlation_id}, content={_content!r})"

    def __str__(self) -> str:
        return self.json(by_alias=True)
