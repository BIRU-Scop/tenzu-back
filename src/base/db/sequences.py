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

"""
This module contains useful functions for managing sequences in tenzu.
"""

from contextlib import closing

from django.db import connection, transaction

from base.db import exceptions as ex


@transaction.atomic
def create(seqname: str, start: int = 1) -> None:
    """
    Create a new sequence.

    :param seqname: the name of the sequence
    :type seqname: str
    :param int start: the value at which the sequence will start (`1` by default)
    :type start: int
    """
    sql = "CREATE SEQUENCE IF NOT EXISTS {} START %s;".format(seqname)

    with closing(connection.cursor()) as cursor:
        cursor.execute(sql, [start])


def exists(seqname: str) -> bool:
    """
    Check if a sequence exists.

    :param seqname: the name of the sequence
    :type seqname: str
    :return `True` if the sequence exists, `False` if not.
    :rtype bool
    """
    sql = """
    SELECT EXISTS(
      SELECT relname FROM pg_class
      WHERE relkind = 'S' AND relname = %s);
    """

    with closing(connection.cursor()) as cursor:
        cursor.execute(sql, [seqname])
        result = cursor.fetchone()
        return result[0]


@transaction.atomic
def next_value(seqname: str) -> int:
    """
    Increase the current value of a sequence and return the next value.

    :param seqname: the name of the sequence
    :type seqname: str
    :return the current sequence value
    :rtype int
    """
    sql = "SELECT nextval(%s);"
    with closing(connection.cursor()) as cursor:
        try:
            cursor.execute(sql, [seqname])
            result = cursor.fetchone()
            return result[0]
        except ex.ProgrammingError:
            raise ex.SequenceDoesNotExist()


def current_value(seqname: str) -> int:
    """
    Get the current value of a sequence.

    :param seqname: the name of the sequence
    :type seqname: str
    :return the current sequence value
    :rtype int
    """
    sql = "SELECT currval(%s);"
    with closing(connection.cursor()) as cursor:
        try:
            cursor.execute(sql, [seqname])
            result = cursor.fetchone()
            return result[0]
        except ex.ProgrammingError:
            raise ex.SequenceDoesNotExist()


@transaction.atomic
def set_value(seqname: str, value: int) -> None:
    """
    Change the current value of a sequence to a new one.

    :param seqname: the name of the sequence
    :type seqname: str
    :param int value: the new value at which the sequence will continue
    :type value: int
    """
    sql = "SELECT setval(%s, %s);"
    with closing(connection.cursor()) as cursor:
        cursor.execute(sql, [seqname, value])


@transaction.atomic
def delete(seqnames: list[str]) -> None:
    """
    Delete a list of sequences.

    :param seqnames: the name of the sequences
    :type seqnames: list[str]
    """
    sql = "DROP SEQUENCE IF EXISTS {};".format(", ".join(seqnames))
    with closing(connection.cursor()) as cursor:
        cursor.execute(sql)
