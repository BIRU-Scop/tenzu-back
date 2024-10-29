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

import functools
import uuid
from typing import Type

from asgiref.sync import sync_to_async

# isort: off
from django.db.models import *  # noqa

# isort: on

from django.apps import apps
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation  # noqa
from django.contrib.contenttypes.models import ContentType  # noqa
from django.contrib.postgres.fields import ArrayField  # noqa
from django.contrib.postgres.lookups import Unaccent  # noqa
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector  # noqa
from django.db.models import Model, UUIDField
from django.db.models.functions import Coalesce, Lower, StrIndex, TruncDate  # noqa

from base.db.models.fields import *  # noqa
from base.utils.uuid import encode_uuid_to_b64str
from configurations.conf import settings

get_model = apps.get_model


def uuid_generator() -> uuid.UUID:
    """uuid.uuid1 wrap function to protect the MAC address."""
    return uuid.uuid1(node=settings.UUID_NODE)


class BaseModel(Model):
    id = UUIDField(
        primary_key=True,
        null=False,
        blank=True,
        default=uuid_generator,
        editable=False,
        verbose_name="ID",
    )

    class Meta:
        abstract = True

    @functools.cached_property
    def b64id(self) -> str:
        return encode_uuid_to_b64str(self.id)


@sync_to_async
def get_contenttype_for_model(model: Model | Type[Model]) -> ContentType:
    return ContentType.objects.get_for_model(model)
