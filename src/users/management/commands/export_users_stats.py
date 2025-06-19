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

import csv
import hashlib
from datetime import datetime
from pathlib import Path
from typing import TextIO

from django.core.management.base import BaseCommand
from django.db.models import Q, QuerySet

from users.models import User


def add_salt(email: str):
    return f"tenzu:{email}"


class Command(BaseCommand):
    help = "Export anonymised users registration, useful for stats without collecting any personal data"

    def add_arguments(self, parser):
        parser.add_argument("file_path", type=Path)

    def get_last_user_exported_date(self, csv_file: TextIO) -> datetime | None:
        last_position = csv_file.tell()
        csv_file.seek(
            max(0, last_position - 50)
        )  # be sure to read full iso-formated date that should be last thing written
        content = csv_file.read()
        last_sep_index = content.rfind(",")
        if last_sep_index == -1:
            raise ValueError("Existing file is not in expected format")
        iso_datetime = content[last_sep_index + 1 :].strip()
        return (
            datetime.fromisoformat(iso_datetime)
            if iso_datetime
            != "date_joined"  # happens when file is empty except for headers
            else None
        )

    def exclude_demo_test_data(self, qs: QuerySet[User]):
        return qs.exclude(
            Q(username__startswith="pruebastenzu")
            | Q(username="admin")
            | Q(email__endswith="@tenzu.demo"),
        )

    def handle(self, *args, **options):
        file_path: Path = options["file_path"]
        qs = self.exclude_demo_test_data(User.objects.all().order_by("date_joined"))

        fieldnames = [
            "email_hash",
            "date_joined",
        ]
        is_existing_file = file_path.exists()

        with file_path.open("a+", newline="") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            if is_existing_file:
                if (
                    start_date := self.get_last_user_exported_date(csv_file)
                ) is not None:
                    qs = qs.filter(date_joined__gt=start_date)
            else:
                writer.writeheader()
            for user in qs.iterator():
                writer.writerow(
                    {
                        "email_hash": hashlib.sha512(
                            add_salt(user.email).encode("utf-8", "backslashreplace")
                        ).hexdigest(),
                        "date_joined": user.date_joined.isoformat(),
                    }
                )
