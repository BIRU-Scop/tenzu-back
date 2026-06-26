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
import logging
from typing import Any
from uuid import UUID

from django.core.exceptions import SuspiciousFileOperation
from django.utils.translation import gettext
from ninja import UploadedFile
from ninja.errors import ValidationError as APIValidationError
from pydantic_core import ErrorDetails

from commons.utils import transaction_atomic_async, transaction_on_commit_async
from import_export import events as import_export_events
from import_export import repositories as import_export_repositories
from import_export.models import (
    ImportationStatus,
    ProjectImportation,
    ProjectImportationType,
)
from import_export.serializers import (
    InvitedProjectImportationSerializer,
    ProjectImportationSerializer,
)
from import_export.services import exceptions as ex
from memberships.api.validators import InvitationsValidator
from memberships.serializers import InvitationBaseSerializer
from projects.invitations import api as projects_invitations_apis
from projects.projects import events as projects_events
from projects.projects import services as projects_services
from users.models import User
from workspaces.workspaces.models import Workspace

logger = logging.getLogger(__name__)


##########################################################
# import project
##########################################################


@transaction_atomic_async
async def import_project(
    user: User,
    workspace: Workspace,
    origin_type: ProjectImportationType,
    source: UploadedFile,
) -> ProjectImportationSerializer:
    try:
        project_importation = (
            await import_export_repositories.create_project_importation(
                user=user,
                workspace=workspace,
                origin_type=origin_type,
                source_file=source,
            )
        )
    except SuspiciousFileOperation as e:
        msg = gettext("Suspicious file, try to shorten the file name")
        raise APIValidationError(
            [
                ErrorDetails(
                    type="suspicious_file_operation",
                    loc=["file", "source"],
                    msg=msg,
                    ctx={"error": msg},
                    input=source.name,
                )
            ]
        ) from e

    # Emit event
    await transaction_on_commit_async(
        import_export_events.emit_event_when_project_importation_is_created
    )(
        project_importation=project_importation,
    )
    match origin_type:
        case ProjectImportationType.TAIGA:
            from import_export.tasks import import_taiga_project

            await import_taiga_project.defer_async(
                project_importation_id=project_importation.b64id,
            )
        case _:
            raise NotImplementedError

    return ProjectImportationSerializer.model_validate(project_importation)


##########################################################
# get project importation
##########################################################


async def get_project_importation(project_importation_id: UUID) -> ProjectImportation:
    return await import_export_repositories.get_project_importation(
        project_importation_id=project_importation_id
    )


##########################################################
# update project importation
##########################################################


async def update_project_importation(
    project_importation: ProjectImportation, values: dict[str, Any] = {}
) -> ProjectImportation:
    updated_project_importation = (
        await import_export_repositories.update_project_importation(
            project_importation=project_importation, values=values
        )
    )
    # Emit event
    await transaction_on_commit_async(
        import_export_events.emit_event_when_project_importation_is_updated
    )(
        project_importation=project_importation,
    )
    return updated_project_importation


async def succeed_project_importation(
    project_importation: ProjectImportation,
) -> ProjectImportation:
    project_importation = await update_project_importation(
        project_importation,
        {"status": ImportationStatus.SUCCESS},
    )
    project_importation.project.user_is_invited = (
        False  # to prevent validation error in event serializer
    )
    await transaction_on_commit_async(
        projects_events.emit_event_when_project_is_created
    )(project=project_importation.project, creator=project_importation.created_by)
    return project_importation


##########################################################
# list project importations
##########################################################


async def list_workspace_project_importations_for_user(
    workspace: Workspace, user: User
) -> list[ProjectImportation]:
    return (
        await import_export_repositories.list_workspace_project_importations_for_user(
            workspace=workspace, user=user
        )
    )


##########################################################
# delete project importation
##########################################################


@transaction_atomic_async
async def delete_project_importation(project_importation: ProjectImportation) -> bool:
    if project_importation.status not in (ImportationStatus.FAILURE,):
        raise ex.IncompatibleImportationStatus()

    if project_importation.project is not None:
        await projects_services.delete_project(
            project_importation.project, deleted_by=project_importation.created_by
        )
    deleted = await import_export_repositories.delete_project_importation(
        project_importation=project_importation
    )

    if deleted > 0:
        # Emit event
        await transaction_on_commit_async(
            import_export_events.emit_event_when_project_importation_is_deleted
        )(
            workspace_id=project_importation.workspace_id,
            project_importation_id=project_importation.id,
            importation_owner=project_importation.created_by,
        )

        return True

    return False


##########################################################
# backport previous users
##########################################################


@transaction_atomic_async
async def handle_project_importation_pending_invites(
    project_importation: ProjectImportation,
    invitations_form: InvitationsValidator,
    request,
) -> InvitedProjectImportationSerializer:
    if project_importation.status not in (ImportationStatus.ACTION_NEEDED,):
        raise ex.IncompatibleImportationStatus()

    invitations: list[InvitationBaseSerializer] = []
    if invitations_form.invitations:
        invitations = (
            await projects_invitations_apis.create_project_invitations(
                request,
                project_importation.project_id,
                invitations_form,
            )
        ).invitations
    project_importation = await succeed_project_importation(
        project_importation,
    )
    return InvitedProjectImportationSerializer(
        invitations=invitations, project_importation=project_importation
    )
