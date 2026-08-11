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

from dataclasses import dataclass
from typing import Final


@dataclass
class Error:
    code: str
    msg: str


EX_VALIDATION_ERROR: Final = Error(
    code="validation-error", msg="Unable to fulfill the request due to semantic errors"
)
EX_UNKNOWN: Final = Error(code="unknown", msg="Unknown error")
EX_NOT_FOUND: Final = Error(
    code="not-found", msg="The requested resource could not be found"
)
EX_CONFLICT: Final = Error(
    code="conflict",
    msg="The request could not be completed due to a conflict with the current state",
)
EX_PRECONDITION_FAILED: Final = Error(
    code="precondition-failed",
    msg="A necessary precondition was not met",
)
EX_CONTENT_TOO_LARGE: Final = Error(
    code="content-too-large",
    msg="The maximum allowed upload size was exceeded",
)
EX_UNSUPPORTED_MEDIA_TYPE: Final = Error(
    code="unsupported-media-type",
    msg="The request used an unsupported content type or encoding",
)
EX_FAILED_DEPENDENCY: Final = Error(
    code="failed-dependency", msg="A required external dependency has failed"
)
EX_AUTHORIZATION: Final = Error(
    code="authorization-error",
    msg="Invalid token or no active account found with the given credentials",
)
EX_FORBIDDEN: Final = Error(
    code="forbidden", msg="The user doesn't have permissions to perform this action"
)
EX_BAD_REQUEST: Final = Error(code="bad-request", msg="The request is incorrect")
EX_LOCKED: Final = Error(
    code="locked",
    msg="The resource is currently locked",
)
EX_INTERNAL_SERVER_ERROR: Final = Error(
    code="internal-server-error", msg="Server error"
)
