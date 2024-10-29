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

from uuid import UUID

from base.utils.uuid import decode_b64str_to_uuid, encode_uuid_to_b64str


def test_encode_uuid_to_b64str():
    id = UUID("e8982c6c-6ca8-11ed-9513-1856806ac8db")
    b64id = "6JgsbGyoEe2VExhWgGrI2w"

    assert encode_uuid_to_b64str(id) == b64id


def test_decode_b64str_to_uuid():
    b64id = "6JgsbGyoEe2VExhWgGrI2w"
    id = UUID("e8982c6c-6ca8-11ed-9513-1856806ac8db")

    assert decode_b64str_to_uuid(b64id) == id
