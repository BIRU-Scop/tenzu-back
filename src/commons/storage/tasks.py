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

from datetime import timedelta

from procrastinate.contrib.django import app

from base.utils.datetime import aware_utcnow
from commons.storage import services as storage_services
from configurations.conf import settings


@app.periodic(cron=settings.STORAGE.CLEAN_DELETED_STORAGE_OBJECTS_CRON)  # type: ignore
@app.task
async def clean_deleted_storaged_objects(timestamp: int) -> int:
    return await storage_services.clean_deleted_storaged_objects(
        before=aware_utcnow()
        - timedelta(days=settings.STORAGE.DAYS_TO_STORE_DELETED_STORAGED_OBJECTS)
    )
