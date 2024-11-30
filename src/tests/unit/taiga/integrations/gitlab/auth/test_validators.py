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

import pytest
from pydantic import ValidationError

from integrations.gitlab.auth.validators import GitlabLoginValidator
from tests.utils.utils import check_validation_errors


def test_validate_gitlab_login_not_available_lang():
    code = "code"
    redirect_uri = "https://redirect.uri"
    lang = "xx"

    with pytest.raises(ValidationError) as validation_errors:
        GitlabLoginValidator(code=code, redirect_uri=redirect_uri, lang=lang)

    expected_error_fields = ["lang"]
    expected_error_messages = ["Language is not available"]
    check_validation_errors(
        validation_errors, expected_error_fields, expected_error_messages
    )
