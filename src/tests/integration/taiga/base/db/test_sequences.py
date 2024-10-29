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

import pytest

from base.db import sequences as seq

pytestmark = pytest.mark.django_db


def test_sequences_common_life_cycle():
    seqname = "foo"

    # Create
    assert not seq.exists(seqname)
    seq.create(seqname)
    assert seq.exists(seqname)

    # Get values
    assert seq.next_value(seqname) == 1
    assert seq.next_value(seqname) == 2
    assert seq.current_value(seqname) == 2
    assert seq.next_value(seqname) == 3

    # Delete sequence
    seq.delete([seqname])
    assert not seq.exists(seqname)


def test_create_with_custom_start_value():
    seqname = "foo"

    # Create
    assert not seq.exists(seqname)
    seq.create(seqname, start=42)
    assert seq.exists(seqname)

    # Get values
    assert seq.next_value(seqname) == 42
    assert seq.next_value(seqname) == 43
    assert seq.current_value(seqname) == 43
    assert seq.next_value(seqname) == 44

    # Delete sequence
    seq.delete([seqname])
    assert not seq.exists(seqname)


def test_change_sequences_value():
    seqname = "foo"

    # Create
    assert not seq.exists(seqname)
    seq.create(seqname)
    assert seq.exists(seqname)

    # Get values
    assert seq.next_value(seqname) == 1
    assert seq.next_value(seqname) == 2
    assert seq.next_value(seqname) == 3

    # Set value
    seq.set_value(seqname, 1)

    # Get value
    assert seq.current_value(seqname) == 1
    assert seq.next_value(seqname) == 2
    assert seq.next_value(seqname) == 3

    # Delete sequence
    seq.delete([seqname])
    assert not seq.exists(seqname)
