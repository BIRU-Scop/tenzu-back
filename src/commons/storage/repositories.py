# -*- coding: utf-8 -*-
# Copyright (C) 2024-2025 BIRU
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
from typing import TypedDict
from uuid import UUID

from django.db.models.deletion import RestrictedError

from base.utils.files import File
from commons.storage.models import StoragedObject
from commons.utils import transaction_atomic_async
from ninja_jwt.utils import aware_utcnow

##########################################################
# filters and querysets
##########################################################


class StoragedObjectFilters(TypedDict, total=False):
    id: UUID
    deleted_at__lt: datetime


##########################################################
# create storaged object
##########################################################


async def create_storaged_object(
    file: File,
) -> StoragedObject:
    return await StoragedObject.objects.acreate(file=file)


##########################################################
# list storaged object
##########################################################


async def list_storaged_objects(
    filters: StoragedObjectFilters = {},
) -> list[StoragedObject]:
    qs = StoragedObject.objects.all().filter(**filters)
    return [so async for so in qs]


##########################################################
# delete storaged object
########################################################


@transaction_atomic_async
async def delete_storaged_object(
    storaged_object: StoragedObject,
) -> bool:
    try:
        await transaction_atomic_async(storaged_object.adelete)()
    except RestrictedError:
        # This happens when you try to delete a StoragedObject that is being used by someone
        # (using ForeignKey with on_delete=PROTECT).
        # TODO: log this
        return False
    else:
        storaged_object.file.delete(save=False)
        return True


def mark_storaged_object_as_deleted(
    storaged_object: StoragedObject,
) -> None:
    storaged_object.deleted_at = aware_utcnow()
    storaged_object.save(update_fields=["deleted_at"])
