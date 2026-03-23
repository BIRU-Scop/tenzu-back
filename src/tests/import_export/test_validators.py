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


import pytest
from pydantic import ValidationError

from import_export.api import ImportProjectValidator
from import_export.models import ImportationType
from tests.utils import factories as f
from tests.utils.utils import check_validation_errors

##########################################################
# ImportProjectValidator
##########################################################


def test_invalid_import():
    import_file = f.build_string_uploadfile()

    with pytest.raises(ValidationError) as validations_errors:
        # noinspection PyTypeChecker
        ImportProjectValidator(origin_type="test", source=import_file)

    expected_error_fields = [
        "source",
        "origin_type",
    ]
    expected_error_messages = [
        "Value error, Invalid importation content type, expected on of application/json",
        f"Input should be {' or '.join(f"'{t}'" for t in ImportationType.values)}",
    ]
    check_validation_errors(
        validations_errors, expected_error_fields, expected_error_messages
    )


def test_valid_import():
    import_file = f.build_string_uploadfile(content_type="application/json")

    # noinspection PyTypeChecker
    ImportProjectValidator(origin_type=ImportationType.TAIGA.value, source=import_file)
