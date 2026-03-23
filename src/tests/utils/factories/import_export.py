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
from import_export.models import ImportationType

from .base import Factory, factory

# IMPORTATION


class ImportationFactory(Factory):
    origin_type = ImportationType.TAIGA
    source = factory.django.FileField(format="json")
    extra_data = factory.LazyFunction(
        lambda: {"workspace_id": encode_uuid_to_b64str(uuid.uuid1())}
    )

    class Meta:
        model = "import_export.Importation"


@sync_to_async
def create_importation(**kwargs):
    return ImportationFactory.create(**kwargs)


def build_importation(**kwargs):
    return ImportationFactory.build(**kwargs)
