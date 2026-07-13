# Copyright (C) 2026 BIRU
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
import re

from django.db import IntegrityError
from ninja import Router

from base.serializers import BaseDataSchema
from commons.exceptions import api as ex
from commons.exceptions.api.errors import ERROR_RESPONSE_422
from feeds import services as feeds_services
from feeds.api.validators import MarkAsReadValidator
from feeds.models import FeedItem, FeedItemReadStatus
from feeds.serializers import FeedItemSerializer, FeedItemUpdateReadSerializer

feeds_router = Router()


##########################################################
# list active feed items
##########################################################


@feeds_router.get(
    "/feeds",
    url_name="feeds.list",
    summary="List the active feed items for the current user",
    response={
        200: BaseDataSchema[list[FeedItemSerializer]],
    },
    by_alias=True,
)
async def list_feed_items(request) -> list[FeedItem]:
    return await feeds_services.list_active_feed_items(user=request.user)


##########################################################
# mark feed items as read
##########################################################


@feeds_router.post(
    "/feeds/read",
    url_name="feeds.mark.read",
    summary="Mark feed items as read for the current user",
    response={
        200: BaseDataSchema[list[FeedItemUpdateReadSerializer]],
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def mark_feed_items_as_read(
    request, payload: MarkAsReadValidator
) -> list[FeedItemReadStatus]:
    try:
        return await feeds_services.mark_feed_items_as_read(
            user=request.user, ids=payload.ids
        )
    except IntegrityError as e:
        # one of the given id was invalid
        invalid_ids = re.search(r"\(feed_item_id\)=\((.+)\)", e.args[0])
        raise ex.NotFoundError(invalid_ids.group(1) if invalid_ids else "") from e
