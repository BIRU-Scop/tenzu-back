# Copyright (C) 2026 BIRU
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

from asgiref.sync import sync_to_async

from base.utils.uuid import encode_uuid_to_b64str
from import_export.models import ImportationStatus, ProjectImportationType

from .base import Factory, factory

# IMPORTATION


class ProjectImportationFactory(Factory):
    status = ImportationStatus.PENDING
    origin_type = ProjectImportationType.TAIGA
    source = factory.django.FileField(format="json")
    created_by = factory.SubFactory("tests.utils.factories.UserFactory")
    workspace = factory.SubFactory(
        "tests.utils.factories.WorkspaceFactory",
        created_by=factory.SelfAttribute("..created_by"),
    )
    project = factory.SubFactory(
        "tests.utils.factories.ProjectFactory",
        created_by=factory.SelfAttribute("..created_by"),
    )
    extra_data = factory.LazyFunction(lambda: {})

    class Meta:
        model = "import_export.Importation"


@sync_to_async
def create_project_importation(**kwargs):
    return ProjectImportationFactory.create(**kwargs)


def build_project_importation(**kwargs):
    return ProjectImportationFactory.build(**kwargs)
