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

from typing import Any, Type
from uuid import UUID

from django.db.models import F

from base.db.models import BaseModel


async def update(
    model_class: Type[BaseModel],
    id: UUID,
    values: dict[str, Any] = {},
    current_version: int | None = None,
    protected_attrs: list[str] = [],
) -> bool:
    updates = dict(values.copy())
    updates["version"] = F("version") + 1

    if len(updates) == 1:
        return False  # Nothing to update

    # check the version if any of the protected attributes are updated
    if set(protected_attrs).intersection(set(updates.keys())):
        qs = model_class.objects.filter(id=id, version=current_version)
    else:
        qs = model_class.objects.filter(id=id)

    num_updates = await qs.aupdate(**updates)

    return num_updates > 0
