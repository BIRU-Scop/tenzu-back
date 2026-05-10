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
import mimetypes
from operator import attrgetter
from pathlib import Path
from typing import Literal
from uuid import UUID

from asgiref.sync import sync_to_async
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import DatabaseError
from pydantic import ValidationError
from slugify import slugify

from attachments import repositories as attachments_repositories
from attachments.repositories import BulkAttachment
from base.utils.slug import generate_incremental_int_suffix
from comments import repositories as comments_repositories
from comments.models import Comment
from commons.colors import ordered_colour_generator
from commons.utils import transaction_atomic_async
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
    _TaigaAttachment,
    _TaigaHistory,
    _TaigaMemberPermission,
)
from import_export.services import (
    succeed_project_importation,
    update_project_importation,
)
from permissions.choices import ProjectPermissions
from projects.projects import services as projects_services
from projects.projects.repositories import ProjectTemplateModel
from stories.assignments import repositories as story_assignments_repositories
from stories.assignments.models import StoryAssignment
from stories.stories import repositories as stories_repositories
from stories.stories.models import Story
from stories.stories.services.blocknote import (
    BlockNoteConverter,
    BlockNoteEmptyOutputError,
)
from workflows import services as workflows_services
from workflows.models import Workflow

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
            created_at=taiga_project.created_date,
        )
        await update_project_importation(project_importation, {"project": project})
        # TODO users data from memberships and owner

        if not taiga_project.is_kanban_activated:
            await succeed_project_importation(project_importation)
            return
        workflows = await workflows_services.list_workflows(project_id=project.id)
        await do_import_taiga_stories(project_importation, workflows, taiga_project)
        await succeed_project_importation(project_importation)
    except (RuntimeError, BlockNoteEmptyOutputError, DatabaseError) as e:
        # TODO those are the errors where a retry of the job should be attempted
        raise e
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


async def do_import_taiga_stories(
    project_importation: ProjectImportation,
    workflows: list[Workflow],
    taiga_project: TaigaProjectImport,
):
    BULK_SIZE = 250
    ids_by_name: dict[str | None, tuple[UUID, dict[str, UUID]]] = {
        workflow.name: (
            workflow.id,
            {status.name: status.id for status in workflow.statuses.all()},
        )
        for workflow in workflows
    }
    ids_by_name[None] = next(
        iter(ids_by_name.values())
    )  # handle the case of no swimlane
    stories_to_create: list[Story] = []
    assignments_to_create: list[StoryAssignment] = []
    attachments_to_create: list[BulkAttachment] = []
    comments_to_create: list[Comment] = []
    attachment_warnings: list[notifications.WarningFileTooBig] = []
    all_to_create = (
        stories_to_create,
        assignments_to_create,
        attachments_to_create,
        comments_to_create,
        attachment_warnings,
    )
    await sync_to_async(ContentType.objects.get_for_model)(
        Story
    )  # fill cache for later generic relation queries (e.g. Comment, Attachment)
    # Start Node.js process once
    with BlockNoteConverter(source_format="md") as converter:
        for taiga_story in taiga_project.user_stories:
            if taiga_story.status is None:
                logger.warning(
                    f"Project import {project_importation.id} for file '{Path(project_importation.source.name or '').name}' has a story without status: #{taiga_story.ref} {taiga_story.subject}"
                )
                continue
            assigned_users = {taiga_story.assigned_to, *taiga_story.assigned_users}
            assigned_users.discard(None)
            # TODO handle users other than owner
            user_id = (
                project_importation.created_by_id
                if project_importation.created_by.email == taiga_story.owner
                else None
            )
            workflow_id, statuses = ids_by_name[taiga_story.swimlane]
            status_id = statuses[taiga_story.status]

            binary_data, block_data = None, None
            if taiga_story.description:
                _, binary_data, block_data = converter.convert(
                    {"id": "0", "content": taiga_story.description}
                )

            story = Story(
                title=taiga_story.subject,
                description=block_data,
                description_binary=binary_data,
                project_id=project_importation.project_id,
                workflow_id=workflow_id,
                status_id=status_id,
                created_by_id=user_id,
                order=taiga_story.kanban_order,
                created_at=taiga_story.created_date,
                description_updated_at=taiga_story.modified_date,
                version=taiga_story.version,
            )
            stories_to_create.append(story)
            if project_importation.created_by.email in assigned_users:
                assignments_to_create.append(
                    StoryAssignment(story=story, user=project_importation.created_by)
                )
            # TODO keep track of other assigned users for later processing
            for taiga_attachment in sorted(
                taiga_story.attachments, key=attrgetter("order")
            ):
                attachment = build_story_attachment_from_taiga(
                    project_importation, story, taiga_attachment, attachment_warnings
                )
                if attachment is not None:
                    attachments_to_create.append(attachment)
            for event in taiga_story.history:
                comment = build_story_comment_from_taiga(
                    converter, project_importation, story, event
                )
                if comment is not None:
                    comments_to_create.append(comment)
            if any(
                len(list_to_create) >= BULK_SIZE for list_to_create in all_to_create
            ):
                await bulk_create_all(
                    project_importation=project_importation,
                    stories_to_create=stories_to_create,
                    assignments_to_create=assignments_to_create,
                    attachments_to_create=attachments_to_create,
                    comments_to_create=comments_to_create,
                    attachment_warnings=attachment_warnings,
                )
                for list_to_create in all_to_create:
                    list_to_create.clear()
    # Flush remaining objects
    await bulk_create_all(
        project_importation=project_importation,
        stories_to_create=stories_to_create,
        assignments_to_create=assignments_to_create,
        attachments_to_create=attachments_to_create,
        comments_to_create=comments_to_create,
        attachment_warnings=attachment_warnings,
    )


@transaction_atomic_async
async def bulk_create_all(
    project_importation: ProjectImportation,
    stories_to_create: list[Story],
    assignments_to_create: list[StoryAssignment],
    attachments_to_create: list[BulkAttachment],
    comments_to_create: list[Comment],
    attachment_warnings: list[notifications.WarningFileTooBig],
):
    if stories_to_create:
        await stories_repositories.bulk_create_stories(
            project_importation.project_id,
            stories_to_create,
        )
    if assignments_to_create:
        await story_assignments_repositories.bulk_create_story_assignments(
            assignments_to_create,
        )
    if attachments_to_create:
        await attachments_repositories.bulk_create_attachments(
            attachments_to_create,
        )
    if comments_to_create:
        await comments_repositories.bulk_create_comments(
            comments_to_create,
        )
    if attachment_warnings:
        await notifications.notify_when_project_importation_file_too_big_warning(
            project_importation, attachment_warnings
        )


def build_story_attachment_from_taiga(
    project_importation: ProjectImportation,
    story: Story,
    attachment: _TaigaAttachment,
    attachment_warnings: list[notifications.WarningFileTooBig],
) -> BulkAttachment | None:
    if attachment.attached_file is None:
        return
    # TODO handle users other than owner
    user = (
        project_importation.created_by
        if project_importation.created_by.email == attachment.owner
        else None
    )
    file = SimpleUploadedFile(
        name=attachment.name,
        content=attachment.attached_file.data,
        content_type=mimetypes.guess_file_type(attachment.attached_file.name)[0]
        or "application/octet-stream",
    )
    if file.size > settings.MAX_UPLOAD_FILE_SIZE:
        attachment_warnings.append({"file_name": file.name, "file_size": file.size})
        return None
    return BulkAttachment(
        file=file,
        content_object=story,
        created_by=user,
    )


def build_story_comment_from_taiga(
    converter: BlockNoteConverter,
    project_importation: ProjectImportation,
    story: Story,
    event: _TaigaHistory,
) -> Comment | None:
    if not event.comment:
        return None
    # TODO handle users other than owner
    user = (
        project_importation.created_by
        if project_importation.created_by.email
        == (event.user[0] if event.user else None)
        else None
    )
    delete_comment_user = (
        project_importation.created_by
        if project_importation.created_by.email
        == (event.delete_comment_user[0] if event.delete_comment_user else None)
        else None
    )

    block_data = ""
    if not event.delete_comment_date:
        _, _, block_data = converter.convert({"id": "0", "content": event.comment})
    return Comment(
        content_object=story,
        text=block_data,
        created_at=event.created_at,
        created_by=user,
        deleted_at=event.delete_comment_date,
        deleted_by=delete_comment_user,
        modified_at=event.edit_comment_date,
    )
