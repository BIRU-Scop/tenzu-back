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

from base.db import exceptions as ex
from base.db import sequences as seq


def get_project_references_seqname(id: UUID) -> str:
    return f"project_references_{id.hex}"


def create_project_references_sequence(project_id: UUID) -> None:
    seqname = get_project_references_seqname(project_id)
    seq.create(seqname)


def get_new_project_reference_id(project_id: UUID) -> int:
    seqname = get_project_references_seqname(project_id)
    try:
        return seq.next_value(seqname)
    except ex.SequenceDoesNotExist:
        seq.create(seqname)
        return seq.next_value(seqname)


def delete_project_references_sequences(project_ids: list[UUID]) -> None:
    seqnames = [get_project_references_seqname(project_id) for project_id in project_ids]
    seq.delete(seqnames)
