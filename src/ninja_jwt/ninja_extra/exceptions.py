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

# Copyright 2021 Ezeudoh Tochukwu
# https://github.com/eadwinCode/django-ninja-jwt
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
The following exceptions taken from ninja_extra.exceptions as a way to decouple
ourselves from ninja_extra.
"""

from typing import Any, Dict, List, Optional, Union, no_type_check

from django.utils.encoding import force_str
from django.utils.translation import gettext_lazy as _
from ninja.errors import HttpError

from ninja_jwt.ninja_extra import status


class ErrorDetail(str):
    """
    A string-like object that can additionally have a code.
    """

    code = None

    def __new__(cls, string: str, code: Optional[Union[str, int]] = None) -> "ErrorDetail":
        self = super().__new__(cls, string)
        self.code = code
        return self

    def __eq__(self, other: object) -> bool:
        r = super().__eq__(other)
        try:
            return r and self.code == other.code  # type: ignore
        except AttributeError:
            return r

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    def __repr__(self) -> str:
        return "ErrorDetail(string=%r, code=%r)" % (
            str(self),
            self.code,
        )

    def __hash__(self) -> Any:
        return hash(str(self))


@no_type_check
def _get_error_details(
    data: Union[List, Dict, "ErrorDetail"],
    default_code: Optional[Union[str, int]] = None,
) -> Union[List["ErrorDetail"], "ErrorDetail", Dict[Any, "ErrorDetail"]]:
    """
    Descend into a nested data structure, forcing any
    lazy translation strings or strings into `ErrorDetail`.
    """
    if isinstance(data, list):
        ret = [_get_error_details(item, default_code) for item in data]
        return ret
    elif isinstance(data, dict):
        ret = {key: _get_error_details(value, default_code) for key, value in data.items()}
        return ret

    text = force_str(data)
    code = getattr(data, "code", default_code)
    return ErrorDetail(text, code)


class APIException(HttpError):
    """
    Base class for Django-Ninja-Extra exceptions.
    Subclasses should provide `.status_code` and `.default_detail` properties.
    """

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = _("A server error occurred.")
    default_code = "error"

    def __init__(
        self,
        detail: Optional[Union[List, Dict, "ErrorDetail", str]] = None,
        code: Optional[Union[str, int]] = None,
    ) -> None:
        if detail is None:
            detail = force_str(self.default_detail)
        if code is None:
            code = self.default_code

        self.detail = _get_error_details(detail, code)

    def __str__(self) -> str:
        return str(self.detail)

    # def get_codes(self) -> Union[str, Dict[Any, Any]]:
    #     """
    #     Return only the code part of the error details.
    #
    #     Eg. {"name": ["required"]}
    #     """
    #     return _get_codes(self.detail)  # type: ignore
    #
    # def get_full_details(self) -> Dict[Any, Any]:
    #     """
    #     Return both the message & code parts of the error details.
    #
    #     Eg. {"name": [{"message": "This field is required.", "code": "required"}]}
    #     """
    #     return _get_full_details(self.detail)  # type: ignore


class AuthenticationFailedBase(APIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = _("Incorrect authentication credentials.")
    default_code = "authentication_failed"
