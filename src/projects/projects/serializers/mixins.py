# -*- coding: utf-8 -*-
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

from urllib.parse import urljoin
from uuid import UUID

from django.conf import settings
from django.urls import reverse_lazy

from base.serializers import BaseModel, FileField
from base.utils.uuid import encode_uuid_to_b64str


class ProjectLogoBaseSerializer(BaseModel):
    logo: FileField | None = None

    @staticmethod
    def resolve_logo(obj):
        if isinstance(obj, dict):
            logo = obj.get("logo")
            obj_id = obj.get("id")
        else:
            logo = obj.logo
            obj_id = obj.id
        if not logo:
            return None
        return urljoin(
            str(settings.BACKEND_URL),
            str(
                reverse_lazy(
                    f"api-{settings.API_VERSION}:project.get.logo",
                    kwargs={
                        "project_id": encode_uuid_to_b64str(obj_id)
                        if isinstance(obj_id, UUID)
                        else obj_id,
                    },
                )
            ),
        )
