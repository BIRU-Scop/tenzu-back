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

from base.repositories.neighbors import Neighbor

DEFAULT_ORDER_OFFSET = 100  # default offset when adding item


class OrderedMixin(models.Model):
    order = models.BigIntegerField(
        default=100,
        null=False,
        blank=False,
        verbose_name="order",
    )

    class Meta:
        abstract = True


def calculate_offset(
    reorder_reference_item: OrderedMixin,
    reorder_place: str,
    total_slots: int,
    neighbors: Neighbor[OrderedMixin],
    order_offset=DEFAULT_ORDER_OFFSET,
) -> tuple[int, int]:
    if reorder_place == "after":
        pre_order = reorder_reference_item.order
        if neighbors.next:
            post_order = neighbors.next.order
        else:
            post_order = pre_order + (order_offset * total_slots)

    elif reorder_place == "before":
        post_order = reorder_reference_item.order
        if neighbors.prev:
            pre_order = neighbors.prev.order
        else:
            pre_order = min(0, post_order - (order_offset * total_slots))

    else:
        raise ValueError(f"reorder_place {reorder_place} is not a valid value")

    offset = (post_order - pre_order) // total_slots
    return offset, pre_order
