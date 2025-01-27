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

from urllib.parse import urljoin

from asgiref.sync import async_to_sync, sync_to_async
from django.conf import settings
from django.db import transaction
from pydantic_core import Url


def get_absolute_url(url: str | Url):
    if str(url).startswith("/"):
        # relative url
        return urljoin(str(settings.BACKEND_URL), url)
    return url


def transaction_atomic_async(func):
    @sync_to_async
    def wrapper(*args, **kwargs):
        with transaction.atomic():
            return async_to_sync(func)(*args, **kwargs)

    return wrapper
