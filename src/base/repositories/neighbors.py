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

from typing import Generic, TypeVar

from asgiref.sync import sync_to_async
from django.core.exceptions import EmptyResultSet, ObjectDoesNotExist
from django.db import connection

from base.db.models import BaseModel, QuerySet

T = TypeVar("T", bound=BaseModel)


class Neighbor(Generic[T]):
    prev: T | None
    next: T | None

    def __init__(self, prev: T | None = None, next: T | None = None) -> None:
        self.next = next
        self.prev = prev


def get_neighbors_sync(
    obj: T, model_queryset: QuerySet[T] | None = None
) -> Neighbor[T]:
    """Get the neighbors of a model instance.

    The neighbors are the objects that are at the left/right of `obj` that also fulfill the queryset.

    :param obj: The object model you want to know its neighbors.
    :param model_queryset: Additional model constraints to be applied to the default queryset.

    :return: Neighbor class object with the previous and next model objects (if any).
    """
    if model_queryset is None:
        model_queryset = type(obj).objects.get_queryset()

    try:
        base_sql, base_params = model_queryset.query.sql_with_params()
    except EmptyResultSet:
        return Neighbor(prev=None, next=None)

    query = """
        SELECT * FROM
                (SELECT "id",
                    ROW_NUMBER() OVER(),
                    LAG("id", 1) OVER() AS prev,
                    LEAD("id", 1) OVER() AS next
                FROM (%s) as ID_AND_ROW)
        AS SELECTED_ID_AND_ROW
        """ % (base_sql)
    query += " WHERE id=%s;"
    params = list(base_params) + [obj.id]

    cursor = connection.cursor()
    cursor.execute(query, params)
    sql_row_result = cursor.fetchone()

    if sql_row_result is None:
        return Neighbor(prev=None, next=None)

    prev_object_id = sql_row_result[2]
    next_object_id = sql_row_result[3]

    try:
        prev = model_queryset.get(id=prev_object_id)
    except ObjectDoesNotExist:
        prev = None

    try:
        next = model_queryset.get(id=next_object_id)
    except ObjectDoesNotExist:
        next = None

    return Neighbor(prev=prev, next=next)


get_neighbors = sync_to_async(get_neighbors_sync)
