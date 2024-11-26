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

from dataclasses import dataclass

from django.conf import settings
from django.http import HttpResponse
from fastapi import Query

from base.serializers import BaseModel


@dataclass
class Pagination:
    offset: int
    limit: int
    total: int


class PaginationQuery(BaseModel):
    offset: int = Query(0, ge=0, description="Page offset number")
    limit: int = Query(
        settings.DEFAULT_PAGE_SIZE,
        ge=1,
        le=settings.MAX_PAGE_SIZE,
        description=f"Page size (max. {settings.MAX_PAGE_SIZE})",
    )


def set_pagination(response: HttpResponse, pagination: Pagination) -> None:
    response.headers["Pagination-Offset"] = str(pagination.offset)
    response.headers["Pagination-Limit"] = str(pagination.limit)
    response.headers["Pagination-Total"] = str(pagination.total)
