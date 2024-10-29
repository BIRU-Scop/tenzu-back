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

import typer

from base.utils import pprint
from base.utils.concurrency import run_async_as_sync
from base.utils.datetime import aware_utcnow
from configurations.conf import settings
from notifications import services as notifications_services

cli = typer.Typer(
    name="Tenzu Notifications commands",
    help="Manage the notifications system of Tenzu.",
    add_completion=True,
)


@cli.command(help="Clean read notifications. Remove entries from DB.")
def clean_read_notifications(
    minutes_to_store_read_notifications: int = typer.Option(
        settings.NOTIFICATIONS.MINUTES_TO_STORE_READ_NOTIFICATIONS,
        "--minutes",
        "-m",
        help="Delete all notification read before the specified minutes",
    ),
) -> None:
    total_deleted = run_async_as_sync(
        notifications_services.clean_read_notifications(
            before=aware_utcnow() - timedelta(minutes=minutes_to_store_read_notifications)
        )
    )

    color = "red" if total_deleted else "white"
    pprint.print(f"Deleted [bold][{color}]{total_deleted}[/{color}][/bold] notifications.")
