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

import logging
from datetime import timedelta

from django.conf import settings
from procrastinate.contrib.django import app

from ninja_jwt.utils import aware_utcnow
from notifications import services as notifications_services

logger = logging.getLogger(__name__)


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
