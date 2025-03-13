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

from stories.stories import permissions as permissions

#####################################################
# is_view_story_permission_deleted
#####################################################


async def test_is_view_story_permission_deleted_false():
    old_permissions = []
    new_permissions = ["view_story"]

    assert (
        await permissions.is_view_story_permission_deleted(
            old_permissions, new_permissions
        )
        is False
    )


async def test_is_view_story_permission_deleted_true():
    old_permissions = ["view_story"]
    new_permissions = []

    assert (
        await permissions.is_view_story_permission_deleted(
            old_permissions, new_permissions
        )
        is True
    )
