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

from django.db import models

from base.db.models import BaseModel
from base.occ.models import VersionedMixin


class SampleOCCItem(BaseModel, VersionedMixin):
    name = models.CharField(max_length=80, null=False, blank=False)
    description = models.CharField(max_length=220, null=True, blank=True)
    is_active = models.BooleanField(default=True, null=False, blank=False)
