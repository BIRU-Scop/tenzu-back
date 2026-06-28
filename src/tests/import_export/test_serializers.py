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
from unittest.mock import Mock

from pydantic import BaseModel

from import_export.models import (
    ImportationStatus,
    ProjectImportation,
    ProjectImportationPendingInvitation,
)
from import_export.serializers import (
    ProjectImportationNestedSerializer,
    ProjectImportationSerializer,
    TaigaProjectImport,
)
from import_export.serializers.nested import ProjectImportationPendingInvitationNested
from import_export.serializers.taiga import FullTaigaProjectImport
from tests.utils.bad_params import NOT_EXISTING_UUID

#######################################################
# TaigaProjectImport
#######################################################


def test_taiga_project_serializer():
    source_path = (
        Path(__file__).resolve().parent / "samples" / "export_from_taiga_project1.json"
    )
    data = TaigaProjectImport.model_validate_json(source_path.read_text())
    assert not FullTaigaProjectImport.filter_unknown_fields(data.__pydantic_extra__)


def test_full_taiga_project_serializer():
    source_path = (
        Path(__file__).resolve().parent / "samples" / "export_from_taiga_project1.json"
    )
    data = FullTaigaProjectImport.model_validate_json(source_path.read_text())
    q = deque()
    q.append(data)
    while q:
        data = q.popleft()
        assert not data.__pydantic_extra__
        for key, value in data:
            if isinstance(value, BaseModel):
                q.append(value)


#######################################################
# ProjectImportationNestedSerializer & ProjectImportationSerializer
#######################################################


def test_source_name():
    common_args = dict(
        id=NOT_EXISTING_UUID,
        status=ImportationStatus.SUCCESS,
        extra_data={},
        project=None,
        pending_invites={},
    )
    mock_file = Mock()
    # we need this because name argument is consumed by the Mock construction otherwise
    # see https://docs.python.org/3/library/unittest.mock.html#mock-names-and-the-name-attribute
    mock_file.name = ""
    assert (
        ProjectImportationSerializer.model_validate(
            ProjectImportation(**common_args, source=mock_file)
        ).source_name
        is None
    )
    mock_file.name = "/this/is/a/path/file.json"
    serializer = ProjectImportationSerializer.model_validate(
        ProjectImportation(**common_args, source=mock_file)
    )
    assert serializer.source_name == "file.json"
    assert (
        ProjectImportationSerializer.model_validate(serializer).source_name
        == "file.json"
    )


def test_pending_invites():
    common_args = dict(
        id=NOT_EXISTING_UUID,
        status=ImportationStatus.SUCCESS,
        extra_data={},
        project=None,
    )
    assert (
        ProjectImportationNestedSerializer.model_validate(
            ProjectImportation(**common_args, pending_invites={})
        ).pending_invites
        == []
    )

    pending_invite = ProjectImportationPendingInvitation(
        role_id=NOT_EXISTING_UUID,
        assigned_stories_ids=[],
        created_stories_ids=[],
        created_attachments_ids=[],
        created_comments_ids=[],
        deleted_comments_ids=[],
    )
    serializer = ProjectImportationNestedSerializer.model_validate(
        ProjectImportation(
            **common_args,
            pending_invites={
                "test@test.com": pending_invite,
                "test2@test.com": pending_invite,
            },
        )
    )
    assert serializer.pending_invites == [
        ProjectImportationPendingInvitationNested(
            email="test@test.com", role_id=NOT_EXISTING_UUID
        ),
        ProjectImportationPendingInvitationNested(
            email="test2@test.com", role_id=NOT_EXISTING_UUID
        ),
    ]
    assert ProjectImportationNestedSerializer.model_validate(
        serializer
    ).pending_invites == [
        ProjectImportationPendingInvitationNested(
            email="test@test.com", role_id=NOT_EXISTING_UUID
        ),
        ProjectImportationPendingInvitationNested(
            email="test2@test.com", role_id=NOT_EXISTING_UUID
        ),
    ]
