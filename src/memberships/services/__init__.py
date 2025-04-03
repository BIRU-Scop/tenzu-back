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

from memberships import repositories as memberships_repositories
from memberships.models import Membership

##########################################################
# misc
##########################################################


async def is_membership_the_only_owner(
    model: type[Membership], membership: Membership
) -> bool:
    if not membership.role.is_owner:
        return False

    return await memberships_repositories.has_other_owner_memberships(
        model=model, exclude_id=membership.id
    )
