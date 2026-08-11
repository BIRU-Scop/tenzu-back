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

from typing import Any, Optional

from ninja.errors import HttpError as NinjaHttpError

from base.utils.strings import to_kebab

from . import codes


class HTTPException(NinjaHttpError):
    detail: Optional[Any] = None
    headers: Optional[dict[str, Any]] = None

    def __init__(
        self,
        status_code: int,
        code: str = codes.EX_UNKNOWN.code,
        msg: str = "",
        detail: Any = None,
        headers: dict[str, Any] | None = None,
    ) -> None:
        if not detail:
            detail = to_kebab(self.__class__.__name__)

        super().__init__(status_code=status_code, message=msg)
        self.code: str = code
        self.detail: str = detail
        self.headers = headers


##########################
# HTTP 400: BAD REQUEST
##########################


class BadRequest(HTTPException):
    def __init__(
        self,
        msg: str = codes.EX_BAD_REQUEST.msg,
        detail: Any = None,
        headers: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            status_code=400,
            code=codes.EX_BAD_REQUEST.code,
            msg=msg,
            detail=detail,
            headers=headers,
        )


##########################
# HTTP 401: UNAUTHORIZED
##########################


class AuthorizationError(HTTPException):
    def __init__(
        self,
        msg: str = codes.EX_AUTHORIZATION.msg,
        headers: dict[str, Any] | None = None,
    ):
        super().__init__(
            status_code=401,
            code=codes.EX_AUTHORIZATION.code,
            msg=msg,
            headers={"WWW-Authenticate": 'Bearer realm="api"', **(headers or {})},
        )


##########################
# HTTP 403: FORBIDDEN
##########################


class ForbiddenError(HTTPException):
    def __init__(
        self,
        msg: str = codes.EX_FORBIDDEN.msg,
        detail: Any = None,
        headers: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            status_code=403,
            code=codes.EX_FORBIDDEN.code,
            msg=msg,
            detail=detail,
            headers=headers,
        )


##########################
# HTTP 404: NOT FOUND
##########################


class NotFoundError(HTTPException):
    def __init__(
        self,
        msg: str = codes.EX_NOT_FOUND.msg,
        headers: dict[str, Any] | None = None,
    ):
        super().__init__(
            status_code=404, code=codes.EX_NOT_FOUND.code, msg=msg, headers=headers
        )


##########################
# HTTP 409: CONFLICT
##########################


class ConflictError(HTTPException):
    def __init__(
        self,
        msg: str = codes.EX_CONFLICT.msg,
        headers: dict[str, Any] | None = None,
    ):
        super().__init__(
            status_code=404, code=codes.EX_CONFLICT.code, msg=msg, headers=headers
        )


##########################
# HTTP 412: PRECONDITION FAILED
##########################


class PreconditionFailed(HTTPException):
    def __init__(
        self,
        msg: str = codes.EX_PRECONDITION_FAILED.msg,
        detail: Any = None,
        headers: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            status_code=412,
            code=codes.EX_PRECONDITION_FAILED.code,
            msg=msg,
            detail=detail,
            headers=headers,
        )


##########################
# HTTP 413: REQUEST ENTITY TOO LARGE
##########################


class ContentTooLarge(HTTPException):
    def __init__(
        self,
        msg: str = codes.EX_CONTENT_TOO_LARGE.msg,
        detail: Any = None,
        headers: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            status_code=413,
            code=codes.EX_CONTENT_TOO_LARGE.code,
            msg=msg,
            detail=detail,
            headers=headers,
        )


##########################
# HTTP 415: UNSUPPORTED MEDIA TYPE
##########################


class UnsupportedMediaType(HTTPException):
    def __init__(
        self,
        msg: str = codes.EX_UNSUPPORTED_MEDIA_TYPE.msg,
        detail: Any = None,
        headers: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            status_code=415,
            code=codes.EX_UNSUPPORTED_MEDIA_TYPE.code,
            msg=msg,
            detail=detail,
            headers=headers,
        )


##############################
# HTTP 422: VALIDATION ERROR
##############################


class ValidationError(HTTPException):
    def __init__(
        self,
        msg: str = codes.EX_VALIDATION_ERROR.msg,
        headers: dict[str, Any] | None = None,
    ):
        super().__init__(
            status_code=422,
            code=codes.EX_VALIDATION_ERROR.code,
            msg=msg,
            headers=headers,
        )


##########################
# HTTP 423: LOCKED
##########################


class ConflictError(HTTPException):
    def __init__(
        self,
        msg: str = codes.EX_LOCKED.msg,
        headers: dict[str, Any] | None = None,
    ):
        super().__init__(
            status_code=404, code=codes.EX_LOCKED.code, msg=msg, headers=headers
        )


##########################
# HTTP 424: FAILED DEPENDENCY
##########################


class FailedDependency(HTTPException):
    def __init__(
        self,
        msg: str = codes.EX_FAILED_DEPENDENCY.msg,
        detail: Any = None,
        headers: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            status_code=424,
            code=codes.EX_FAILED_DEPENDENCY.code,
            msg=msg,
            detail=detail,
            headers=headers,
        )
