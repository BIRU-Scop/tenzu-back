# -*- coding: utf-8 -*-
# Copyright (C) 2024-2025 BIRU
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

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

from . import codes

#
# Error types to model additional responses in OpenAPI (Swagger)
# Check statuses in https://github.com/encode/starlette/blob/master/starlette/status.py

T = TypeVar("T")


class GenericListError(BaseModel):
    code: str
    detail: list[dict[str, Any]] = [
        {"loc": ["string"], "msg": "string", "type": "string"}
    ]
    msg: str


class GenericSingleError(BaseModel):
    code: str
    detail: str = "string"
    msg: str


class ErrorResponse(BaseModel, Generic[T]):
    error: T


class NotFoundErrorModel(GenericSingleError):
    code: str = codes.EX_NOT_FOUND.code
    msg: str = codes.EX_NOT_FOUND.msg


class UnprocessableEntityModel(GenericListError):
    code: str = codes.EX_VALIDATION_ERROR.code
    msg: str = codes.EX_VALIDATION_ERROR.msg


class UnauthorizedErrorModel(GenericSingleError):
    code: str = codes.EX_AUTHORIZATION.code
    msg: str = codes.EX_AUTHORIZATION.msg


class ForbiddenErrorModel(GenericSingleError):
    code: str = codes.EX_FORBIDDEN.code
    msg: str = codes.EX_FORBIDDEN.msg


class BadRequestErrorModel(GenericSingleError):
    code: str = codes.EX_BAD_REQUEST.code
    msg: str = codes.EX_BAD_REQUEST.msg


class FailedDependencyModel(GenericSingleError):
    code: str = codes.EX_FAILED_DEPENDENCY.code
    msg: str = codes.EX_FAILED_DEPENDENCY.msg


ErrorsDict = dict[int | str, dict[str, type[ErrorResponse[Any]]]]

ERROR_RESPONSE_400 = ErrorResponse[BadRequestErrorModel]
ERROR_RESPONSE_401 = ErrorResponse[UnauthorizedErrorModel]
ERROR_RESPONSE_403 = ErrorResponse[ForbiddenErrorModel]
ERROR_RESPONSE_404 = ErrorResponse[NotFoundErrorModel]
ERROR_RESPONSE_422 = ErrorResponse[UnprocessableEntityModel]
ERROR_RESPONSE_424 = ErrorResponse[FailedDependencyModel]

ERROR_400: ErrorsDict = {400: {"model": ERROR_RESPONSE_400}}
ERROR_401: ErrorsDict = {401: {"model": ERROR_RESPONSE_401}}
ERROR_403: ErrorsDict = {403: {"model": ERROR_RESPONSE_403}}
ERROR_404: ErrorsDict = {404: {"model": ERROR_RESPONSE_404}}
ERROR_422: ErrorsDict = {422: {"model": ERROR_RESPONSE_422}}
ERROR_424: ErrorsDict = {424: {"model": ERROR_RESPONSE_424}}
