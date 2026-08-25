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

from io import BytesIO

from django.http.multipartparser import ChunkIter, LazyStream

from commons.utils.iterators import min_chunk_lazystream, split_by_n


def test_split_by_n():
    assert [x for x in split_by_n("abcdefgh", 2)] == ["ab", "cd", "ef", "gh"]
    assert [x for x in split_by_n("abcdefg", 2)] == ["ab", "cd", "ef", "g"]
    assert [x for x in split_by_n("abcdefg", 3)] == ["abc", "def", "g"]
    assert [x for x in split_by_n("", 3)] == []


def test_min_chunk_lazystream():
    stream = LazyStream(ChunkIter(BytesIO(b"abcdefg"), 3))
    assert [x for x in min_chunk_lazystream(stream, 2)] == [b"abc", b"defg"]
    stream = LazyStream(ChunkIter(BytesIO(b"abcdefg"), 3))
    assert [x for x in min_chunk_lazystream(stream, 1)] == [b"abc", b"def", b"g"]
    stream = LazyStream(ChunkIter(BytesIO(b"abcdef"), 3))
    assert [x for x in min_chunk_lazystream(stream, 2)] == [b"abc", b"def"]
