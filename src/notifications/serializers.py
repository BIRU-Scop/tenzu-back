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

from datetime import datetime

from pydantic import ConfigDict

from base.serializers import UUIDB64, BaseModel, CamelizeDict
from users.serializers.nested import UserNestedSerializer


class NotificationSerializer(BaseModel):
    id: UUIDB64
    type: str
    created_by: UserNestedSerializer | None = None
    created_at: datetime
    read_at: datetime | None = None
    content: CamelizeDict
    model_config = ConfigDict(from_attributes=True)


class NotificationCountersSerializer(BaseModel):
    read: int
    unread: int
    total: int
