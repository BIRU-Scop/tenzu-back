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
from collections import deque
from pathlib import Path

from pydantic import BaseModel

from import_export.serializers import TaigaProjectImport

#######################################################
# TaigaProjectImport
#######################################################


def test_taiga_project_serializer():
    source_path = (
        Path(__file__).resolve().parent / "samples" / "export_from_taiga_project1.json"
    )
    data = TaigaProjectImport.model_validate_json(source_path.read_text())
    q = deque()
    q.append(data)
    while q:
        data = q.popleft()
        assert not data.__pydantic_extra__
        for key, value in data:
            if isinstance(value, BaseModel):
                q.append(value)
