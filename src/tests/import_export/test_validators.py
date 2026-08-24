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

from base.serializers import BaseSchema
from import_export.api.validators import (
    ImportationFileField,
    ImportProjectValidator,
    _ImportProjectValidator,
)
from import_export.models import ProjectImportationType
from tests.utils import factories as f
from tests.utils.utils import check_validation_errors

##########################################################
# ImportProjectValidator
##########################################################


class ImportDataValidator(BaseSchema):
    metadata: ImportProjectValidator


def test_invalid_import():
    with pytest.raises(ValidationError) as validations_errors:
        # noinspection PyTypeChecker
        _ImportProjectValidator(
            origin_type="test", filename="test.json", filetype="application/json"
        )

    expected_error_fields = [
        "origin_type",
    ]
    enum_values = [f"'{t}'" for t in ProjectImportationType.values]
    expected_error_messages = [
        f"Input should be {', '.join(enum_values[:-1]) + ' or ' + enum_values[-1]}",
    ]
    check_validation_errors(
        validations_errors, expected_error_fields, expected_error_messages
    )
    with pytest.raises(ValidationError) as validations_errors:
        # noinspection PyTypeChecker
        _ImportProjectValidator(
            origin_type=ProjectImportationType.TAIGA.value,
            filename="test.json",
            filetype="image/gif",
        )

    expected_error_fields = [
        "filetype",
    ]
    expected_error_messages = [
        f"Input should be 'application/json'",
    ]
    check_validation_errors(
        validations_errors, expected_error_fields, expected_error_messages
    )


def test_valid_import():
    import_file = f.build_string_uploadfile(content_type="application/json")

    # noinspection PyTypeChecker
    _ImportProjectValidator(
        origin_type=ProjectImportationType.TAIGA.value,
        filename="test.json",
        filetype="application/json",
    )
    ImportationFileField(import_file)


def test_metadata():
    ImportDataValidator(
        metadata="originType VEE=,filename Zm9vLmpzb24=,filetype YXBwbGljYXRpb24vanNvbg=="
    )

    with pytest.raises(ValidationError) as validations_errors:
        ImportDataValidator(metadata="key invalid")

    expected_error_fields = [
        "metadata",
    ]
    expected_error_messages = [
        "Value error, Incorrect padding",
    ]
    check_validation_errors(
        validations_errors, expected_error_fields, expected_error_messages
    )

    with pytest.raises(ValidationError) as validations_errors:
        ImportDataValidator(metadata="test")

    expected_error_fields = [
        "metadata.originType",
        "metadata.filename",
        "metadata.filetype",
    ]
    expected_error_messages = ["Field required"] * 3
    check_validation_errors(
        validations_errors, expected_error_fields, expected_error_messages
    )
