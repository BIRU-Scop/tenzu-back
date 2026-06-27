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
from pathlib import Path
from typing import TypedDict

from pydantic import EmailStr, field_validator

from base.serializers import UUIDB64, BaseSchema
from import_export.models import (
    ImportationStatus,
    ProjectImportation,
    ProjectImportationData,
    ProjectImportationPendingInvitation,
)
from projects.projects.serializers.nested import ProjectNestedSerializer


class ProjectImportationPendingInvitationNested(TypedDict, total=True):
    email: EmailStr
    role_id: UUIDB64


class ProjectImportationNestedSerializer(BaseSchema):
    id: UUIDB64
    status: ImportationStatus
    extra_data: ProjectImportationData
    source_name: str | None
    project: ProjectNestedSerializer | None
    pending_invites: (
        dict[EmailStr, ProjectImportationPendingInvitation]
        | list[ProjectImportationPendingInvitationNested]
    )

    @staticmethod
    def resolve_source_name(
        obj: "ProjectImportation | ProjectImportationNestedSerializer",
    ) -> str | None:
        source_name = getattr(obj, "source_name", None)
        if source_name is not None:
            # This happens when serializer is called on already serialized object
            return source_name
        return Path(obj.source.name).name if obj.source.name else None

    @field_validator("pending_invites", mode="after")
    @classmethod
    def to_list(
        cls,
        value: dict[EmailStr, ProjectImportationPendingInvitation]
        | list[ProjectImportationPendingInvitationNested],
    ) -> list[ProjectImportationPendingInvitationNested]:
        if isinstance(value, list):
            # This happens when serializer is called on already serialized object
            return value
        return [
            ProjectImportationPendingInvitationNested(
                email=email, role_id=pending_invitation["role_id"]
            )
            for email, pending_invitation in value.items()
        ]
