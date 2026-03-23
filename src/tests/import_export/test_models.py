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

from unittest.mock import patch

from import_export.models import Importation, get_error_result_file_path
from permissions.choices import ProjectPermissions
from projects.projects import services
from tests.utils import factories as f
from tests.utils.utils import patch_db_transaction


async def test_get_error_result_file_path():
    source_file = f.build_string_file(name="test", format="json")
    assert (
        get_error_result_file_path(Importation(source=source_file), "", "")
        == "test.error_result.json"
    )
    source_file = f.build_string_file(name="a/more/complex/path/test", format="json")
    assert (
        get_error_result_file_path(Importation(source=source_file), "", "")
        == "a/more/complex/path/test.error_result.json"
    )
