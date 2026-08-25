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

from typing import Generator

from django.http.multipartparser import LazyStream


def split_by_n(seq: str, n: int) -> Generator[str, str, None]:
    """
    A generator to divide a sequence into chunks of n units.
    """
    while seq:
        yield seq[:n]
        seq = seq[n:]


def min_chunk_lazystream(stream: LazyStream, min_size: int | None):
    """
    Iterate on a stream and optionally merge last and before last chunks if
    last chunk alone would make it smaller than given min_size constraint.
    Expect the size of all other chunks but the last to be >= min_size
    """
    if min_size is None:
        yield from stream

    for chunk in stream:
        for next_chunk in stream:
            if len(next_chunk) < min_size:
                # next chunk would be too small, we merge it with current one
                chunk += next_chunk
            else:
                # otherwise we undo our read
                stream.unget(next_chunk)
            break
        yield chunk
