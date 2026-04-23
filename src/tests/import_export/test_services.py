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
import uuid
from unittest.mock import patch

from import_export import services
from import_export.serializers import ProjectImportationDetailSerializer
from tests.utils import factories as f

##########################################################
# import_project
##########################################################


async def test_import_project():
    workspace = f.build_workspace()
    importation = f.build_project_importation(
        extra_data={"workspace_id": workspace.b64id}
    )
    user = importation.created_by

    with (
        patch(
            "import_export.services.import_export_repositories", autospec=True
        ) as fake_import_export_repositories,
    ):
        fake_import_export_repositories.create_importation.return_value = importation
        serialised_importation = await services.import_project(
            user=user,
            workspace=workspace,
            origin_type=importation.origin_type,
            source=importation.source,
        )

        # TODO test more once logic is put into place

        assert isinstance(serialised_importation, ProjectImportationDetailSerializer)


##########################################################
# get_importation
##########################################################


async def test_get_importation():
    with (
        patch(
            "import_export.services.import_export_repositories", autospec=True
        ) as fake_import_export_repositories,
    ):
        await services.get_project_importation(project_importation_id=uuid.uuid1())
        fake_import_export_repositories.get_importation.assert_called()
