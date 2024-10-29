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

from asgiref.sync import sync_to_async

from .base import Factory, factory


class StoragedObjectFactory(Factory):
    file = factory.django.ImageField(format="PNG")

    class Meta:
        model = "storage.StoragedObject"


@sync_to_async
def create_storaged_object(**kwargs):
    return StoragedObjectFactory.create(**kwargs)


def build_storaged_object(**kwargs):
    return StoragedObjectFactory.build(**kwargs)
