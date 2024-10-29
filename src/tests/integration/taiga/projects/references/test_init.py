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

from uuid import uuid1

import pytest

from base.db import sequences as seq
from projects import references as refs

pytestmark = pytest.mark.django_db


def test_get_project_references_seqname():
    project1_id = uuid1()
    project2_id = uuid1()

    seqname1 = refs.get_project_references_seqname(project1_id)
    seqname2 = refs.get_project_references_seqname(project2_id)

    assert project1_id.hex in seqname1
    assert project2_id.hex in seqname2


def test_create_project_references_sequence():
    project1_id = uuid1()
    project2_id = uuid1()

    refs.create_project_references_sequence(project1_id)
    refs.create_project_references_sequence(project2_id)

    assert refs.get_new_project_reference_id(project1_id) == 1
    assert refs.get_new_project_reference_id(project2_id) == 1
    assert refs.get_new_project_reference_id(project2_id) == 2

    refs.create_project_references_sequence(project1_id)  # do nothing
    refs.create_project_references_sequence(project2_id)  # do nothing

    assert refs.get_new_project_reference_id(project2_id) == 3
    assert refs.get_new_project_reference_id(project1_id) == 2


def test_get_new_project_reference_id_if_sequence_does_not_exist():
    project_id = uuid1()
    seqname = refs.get_project_references_seqname(project_id)

    assert not seq.exists(seqname)
    assert refs.get_new_project_reference_id(project_id) == 1
    assert seq.exists(seqname)


def test_delete_project_references_sequence():
    project_id = uuid1()

    refs.create_project_references_sequence(project_id)

    refs.delete_project_references_sequences([project_id])
    assert not seq.exists(refs.get_project_references_seqname(project_id))
