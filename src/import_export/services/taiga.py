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
from pathlib import Path
from typing import Literal

from django.core.files.uploadedfile import SimpleUploadedFile
from pydantic import ValidationError
from slugify import slugify

from base.utils.slug import generate_incremental_int_suffix
from commons.colors import ordered_colour_generator
from commons.utils import transaction_on_commit_async
from import_export import notifications
from import_export.models import (
    ImportationError,
    ImportationStatus,
    ProjectImportation,
)
from import_export.serializers import (
    TaigaProjectImport,
)
from import_export.serializers.taiga import (
    FullTaigaProjectImport,
    _TaigaMemberPermission,
)
from import_export.services import update_project_importation
from permissions.choices import ProjectPermissions
from projects.projects import events as projects_events
from projects.projects import services as projects_services
from projects.projects.repositories import ProjectTemplateModel

logger = logging.getLogger(__name__)

_TaigaPermissionMap: dict[_TaigaMemberPermission, ProjectPermissions] = {
    "view_us": ProjectPermissions.VIEW_STORY,
    "add_us": ProjectPermissions.CREATE_STORY,
    "modify_us": ProjectPermissions.MODIFY_STORY,
    "comment_us": ProjectPermissions.CREATE_MODIFY_DELETE_COMMENT,
    "delete_us": ProjectPermissions.DELETE_STORY,
}


def convert_to_tenzu_permissions(
    permissions: list[_TaigaMemberPermission],
) -> list[ProjectPermissions]:
    tenzu_perms = set()
    for perm in permissions:
        tenzu_perms.add(_TaigaPermissionMap.get(perm, None))
    # ignore None value
    tenzu_perms.discard(None)
    # add eventual missing dependencies to ensure a healthy permissions set
    for permission, required_permission in ProjectPermissions.dependencies():
        if permission in tenzu_perms and required_permission not in tenzu_perms:
            tenzu_perms.add(required_permission)
    return list(tenzu_perms)


def ensure_roles_unique_attributes(tenzu_roles, taiga_roles):
    # prevent any duplicate identifying value between default static roles from Tenzu and dynamic ones from Taiga
    attribute: Literal["slug", "name"]
    for attribute, prefix in (("slug", "taiga-"), ("name", "Taiga ")):
        values_from_tenzu = set(role[attribute] for role in tenzu_roles)
        values_from_taiga = set(role[attribute] for role in taiga_roles)
        values_from_both = values_from_tenzu | values_from_taiga
        for role in taiga_roles:
            if (old_value := role[attribute]) in values_from_tenzu:
                suffix_generator = generate_incremental_int_suffix()
                for suffix in suffix_generator:
                    new_value = f"{prefix}{old_value}{suffix}"
                    if new_value not in values_from_both:
                        role[attribute] = new_value
                        break


async def get_template_from_taiga_project(
    taiga_project: TaigaProjectImport,
) -> ProjectTemplateModel:
    default_template = await projects_services._get_default_template()
    default_roles = [role for role in default_template.roles if not role["editable"]]

    serialized_project = taiga_project.model_dump(
        include={"roles", "us_statuses", "swimlanes"}, exclude_unset=False
    )
    for role in serialized_project["roles"]:
        role["editable"] = True
        role["is_owner"] = False
        role["permissions"] = convert_to_tenzu_permissions(role["permissions"])
        del role["computable"]
    for swimlane in serialized_project["swimlanes"]:
        swimlane["slug"] = slugify(swimlane["name"])
        del swimlane["statuses"]
    for status, colour in zip(
        serialized_project["us_statuses"], ordered_colour_generator()
    ):
        # no strong need for clever colour correspondance, it's probably acceptable to lose the hex colour from taiga
        status["color"] = colour
        del status["wip_limit"]
        del status["is_archived"]
        del status["is_closed"]
        del status["slug"]

    ensure_roles_unique_attributes(
        default_roles, serialized_project["roles"]
    )  # TODO, handle potential change in role names, needed afterwards by memberships

    template: ProjectTemplateModel = ProjectTemplateModel.model_construct(
        roles=[*default_roles, *serialized_project["roles"]],
        workflows=serialized_project["swimlanes"] or default_template.workflows,
        workflow_statuses=serialized_project["us_statuses"],
    )
    return template


async def do_import_taiga_project(project_importation: ProjectImportation):
    with project_importation.source.open() as source_file:
        try:
            taiga_project = TaigaProjectImport.model_validate_json(source_file.read())
        except ValidationError as e:
            await update_project_importation(
                project_importation,
                {
                    "status": ImportationStatus.FAILURE,
                    "extra_data": {"error_code": ImportationError.INVALID},
                },
            )
            await notifications.notify_when_project_importation_fail(
                project_importation
            )
            logger.warning(
                f"Project import {project_importation.id} for file '{Path(project_importation.source.name or '').name}' validation failed: {e}"
            )
            return

    try:
        extra_fields = FullTaigaProjectImport.filter_unknown_fields(
            taiga_project.__pydantic_extra__
        )
        if extra_fields:
            logger.warning(
                f"Project import {project_importation.id} for file '{Path(project_importation.source.name or '').name}' contains extra data: {extra_fields}"
            )

        await update_project_importation(
            project_importation, {"status": ImportationStatus.ONGOING}
        )
        project = await projects_services._create_project(
            template=await get_template_from_taiga_project(taiga_project),
            workspace=project_importation.workspace,
            name=taiga_project.name,
            description=taiga_project.description,
            created_by=project_importation.created_by,
            color=None,
            logo_file=SimpleUploadedFile(
                taiga_project.logo.name, taiga_project.logo.data
            )
            if taiga_project.logo is not None
            else None,
        )
        project = await projects_services._update_project(
            project, {"created_at": taiga_project.created_date}
        )
        await update_project_importation(project_importation, {"project": project})
        # TODO users

        if not taiga_project.is_kanban_activated:
            await update_project_importation(
                project_importation,
                {"status": ImportationStatus.SUCCESS},
            )
            await transaction_on_commit_async(
                projects_events.emit_event_when_project_is_created
            )(project=project)
            return
        # TODO stories
    except Exception as e:
        await update_project_importation(
            project_importation,
            {
                "status": ImportationStatus.FAILURE,
                "extra_data": {"error_code": ImportationError.SERVER_ERROR},
            },
        )
        await notifications.notify_when_project_importation_fail(project_importation)
        raise e
