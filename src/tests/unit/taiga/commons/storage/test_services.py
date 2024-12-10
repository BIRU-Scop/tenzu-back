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
from unittest.mock import call, patch

from base.utils.datetime import aware_utcnow
from commons.storage import services
from tests.utils import factories as f


async def test_clean_deleted_storaged_objects():
    storaged_objects = [
        f.build_storaged_object(),
        f.build_storaged_object(),
    ]
    before_datetime = aware_utcnow() - timedelta(days=1)

    with patch(
        "commons.storage.services.storage_repositories", autospec=True
    ) as fake_storage_repositories:
        fake_storage_repositories.list_storaged_objects.return_value = storaged_objects
        fake_storage_repositories.delete_storaged_object.return_value = True

        assert (
            await services.clean_deleted_storaged_objects(before=before_datetime) == 2
        )

        fake_storage_repositories.list_storaged_objects.assert_awaited_once_with(
            filters={"deleted_before": before_datetime}
        )

        fake_storage_repositories.delete_storaged_object.assert_has_awaits(
            [
                call(storaged_objects[0]),
                call(storaged_objects[1]),
            ],
        )
