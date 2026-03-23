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
from uuid import uuid1

import pytest

from import_export import repositories
from import_export.models import Importation, ImportationType
from tests.utils import factories as f
from tests.utils.bad_params import NOT_EXISTING_UUID

pytestmark = pytest.mark.django_db


##########################################################
# create_importation
##########################################################


async def test_create_importation():
    source_file = f.build_string_file()
    workspace = await f.create_workspace()
    user = await f.create_user()
    importation = await repositories.create_importation(
        user=user,
        workspace=workspace,
        origin_type=ImportationType.TAIGA,
        source_file=source_file,
    )
    assert importation.source.name.endswith(source_file.name)
    assert importation.created_by_id == user.id
    assert importation.extra_data == {"workspace_id": workspace.b64id}
    return importation


##########################################################
# get_importation
##########################################################


async def test_get_importation_return_importation():
    importation = await test_create_importation()
    assert (
        await repositories.get_importation(importation_id=importation.id) == importation
    )


async def test_get_importation_not_exists():
    with pytest.raises(Importation.DoesNotExist):
        await repositories.get_importation(importation_id=NOT_EXISTING_UUID)
