# -*- coding: utf-8 -*-
# Copyright (C) 2024 BIRU
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

from datetime import datetime

from commons.storage import repositories as storage_repositories


async def clean_deleted_storaged_objects(before: datetime) -> int:
    storaged_objects = await storage_repositories.list_storaged_objects(
        filters={"deleted_at__lt": before}
    )
    deleted = 0
    for storaged_object in storaged_objects:
        if await storage_repositories.delete_storaged_object(
            storaged_object=storaged_object
        ):
            deleted += 1

    return deleted
