# -*- coding: utf-8 -*-
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

import functools
import uuid
from typing import Type

from asgiref.sync import sync_to_async
from django.contrib.contenttypes.models import ContentType
from django.db import models

from base.db.models.fields import *  # noqa
from commons.utils.uuid import encode_uuid_to_b64str


class BaseDBManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().fetch_mode(models.FETCH_RAISE)


class BaseDBModel(models.Model):
    id = models.UUIDField(
        primary_key=True,
        null=False,
        blank=True,
        default=uuid.uuid7,  # TODO Try to replace with django.db.models.functions.UUIDv7 db_default once on postgres 18
        editable=False,
        verbose_name="ID",
    )
    objects = BaseDBManager()

    class Meta:
        abstract = True

    @functools.cached_property
    def b64id(self) -> str:
        return encode_uuid_to_b64str(self.id)


@sync_to_async
def get_contenttype_for_model(model: models.Model | Type[models.Model]) -> ContentType:
    return ContentType.objects.get_for_model(model)
