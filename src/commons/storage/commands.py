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
from commons.storage import services as storage_services
from configurations.conf import settings

cli = typer.Typer(
    name="Tenzu Storage commands",
    help="Manage the storage system of Tenzu.",
    add_completion=True,
)


@cli.command(help="Clean deleted storaged object. Remove entries from DB and files from storage")
def clean_storaged_objects(
    days_to_store_deleted_storaged_object: int = typer.Option(
        settings.STORAGE.DAYS_TO_STORE_DELETED_STORAGED_OBJECTS,
        "--days",
        "-d",
        help="Delete all storaged object deleted before the specified days",
    ),
) -> None:
    total_deleted = run_async_as_sync(
        storage_services.clean_deleted_storaged_objects(
            before=aware_utcnow() - timedelta(days=days_to_store_deleted_storaged_object)
        )
    )

    color = "red" if total_deleted else "white"
    pprint.print(f"Deleted [bold][{color}]{total_deleted}[/{color}][/bold] storaged objects.")
