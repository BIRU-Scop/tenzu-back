# -*- coding: utf-8 -*-
# Copyright (C) 2024-2025 BIRU
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

from ninja import Router

from base.serializers import BaseDataModel
from system import services as system_services
from system.serializers import LanguageSerializer

system_router = Router()

################################################
# list languages info
################################################


@system_router.get(
    "/system/languages",
    url_name="system.languages.list",
    summary="List system available languages",
    response=BaseDataModel[list[LanguageSerializer]],
    auth=None,
    by_alias=True,
)
async def list_languages(request) -> list[LanguageSerializer]:
    return system_services.get_available_languages_info()
