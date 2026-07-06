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
from collections.abc import Iterable
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django.contrib.admin import AdminSite

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


def restrict_admin_registry(site: AdminSite, keep_labels: Iterable[str]) -> list[str]:
    keep = set(keep_labels)
    unregistered: list[str] = []
    for model in list(site._registry):
        label = model._meta.label
        if label not in keep:
            site.unregister(model)
            unregistered.append(label)
    return unregistered


def add_ending_slash(url: str) -> str:
    if url.endswith("/"):
        return url
    return f"{url}/"


def remove_ending_slash(url: str) -> str:
    return url.rstrip("/")
