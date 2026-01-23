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

from import_export.serializers.taiga import TaigaProjectImport  # noqa
from pydantic import ConfigDict

from base.serializers import BaseModel, FileField

from import_export.models import ImportationType, ImportationStatus


class ImportationDetailSerializer(BaseModel):
    origin_type: ImportationType
    status: ImportationStatus
    source: FileField
    error_result_file: FileField | None = None
    extra_data: dict

    model_config = ConfigDict(from_attributes=True)
