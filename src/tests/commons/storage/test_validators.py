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
from commons.storage.api.validators import TusMetadata
from tests.utils.utils import check_validation_errors

##########################################################
# TusMetadata
##########################################################


class TusUploadValidator(BaseSchema):
    metadata: TusMetadata


def test_metadata():
    TusUploadValidator(metadata="test")
    TusUploadValidator(metadata="key1 dmFsdWUx,key2,key3 dmFsdWUz")

    with pytest.raises(ValidationError) as validations_errors:
        TusUploadValidator(metadata="key invalid")

    expected_error_fields = [
        "metadata",
    ]
    expected_error_messages = [
        "Value error, Incorrect padding",
    ]
    check_validation_errors(
        validations_errors, expected_error_fields, expected_error_messages
    )
