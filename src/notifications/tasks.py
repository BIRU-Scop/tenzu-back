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
# # -*- coding: utf-8 -*-
# # This Source Code Form is subject to the terms of the Mozilla Public
# # License, v. 2.0. If a copy of the MPL was not distributed with this
# # file, You can obtain one at http://mozilla.org/MPL/2.0/.
# #
# # Copyright (c) 2023-present Kaleidos INC
#
import logging
from datetime import timedelta

from procrastinate.contrib.django import app

#
from base.utils.datetime import aware_utcnow
from django.conf import settings
from notifications import services as notifications_services

#
logger = logging.getLogger(__name__)


#
#
@app.periodic(cron=settings.NOTIFICATIONS.CLEAN_READ_NOTIFICATIONS_CRON)  # type: ignore
@app.task
async def clean_read_notifications(timestamp: int) -> int:
    total_deleted = await notifications_services.clean_read_notifications(
        before=aware_utcnow()
        - timedelta(minutes=settings.NOTIFICATIONS.MINUTES_TO_STORE_READ_NOTIFICATIONS)
    )

    logger.info(
        "deleted notifications: %s",
        total_deleted,
        extra={"deleted": total_deleted},
    )

    return total_deleted
