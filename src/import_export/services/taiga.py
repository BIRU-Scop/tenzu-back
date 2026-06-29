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
from typing import Generic, Literal, TypedDict, TypeVar
from uuid import UUID

from asgiref.sync import sync_to_async
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import DatabaseError
from pydantic import EmailStr, ValidationError
from slugify import slugify

from attachments import repositories as attachments_repositories
from attachments.models import Attachment
from base.db.models import BaseDBModel
from base.utils.slug import generate_incremental_int_suffix
from comments import repositories as comments_repositories
from comments.models import Comment
from commons.colors import ordered_colour_generator
from commons.storage.models import StoragedObject
from commons.utils import transaction_atomic_async
from import_export import notifications
from import_export.models import (
    ImportationError,
    ImportationStatus,
    ProjectImportation,
    ProjectImportationPendingInvitation,
)
from import_export.serializers import (
    FullTaigaProjectImport,
)
from import_export.serializers.taiga import (
    _TaigaAttachment,
    _TaigaHistory,
    _TaigaMemberPermission,
    _TaigaUserStory,
)
from import_export.services import (
    succeed_project_importation,
    update_project_importation,
)
from permissions.choices import ProjectPermissions
from projects.memberships.models import ProjectRole
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

T = TypeVar("T", bound=BaseDBModel)


class ProjectImportationPendingObject(Generic[T], TypedDict, total=True):
    user_email: EmailStr
    db_object: T


class ProjectImportationPendingData(TypedDict, total=True):
    assigned_stories: list[ProjectImportationPendingObject[Story]]
    created_stories: list[ProjectImportationPendingObject[Story]]
    created_attachments: list[ProjectImportationPendingObject[Attachment]]
    created_comments: list[ProjectImportationPendingObject[Comment]]
    deleted_comments: list[ProjectImportationPendingObject[Comment]]


_IMPORTATION_BULK_SIZE = 250


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


def ensure_roles_unique_attributes(
    tenzu_roles, taiga_roles
) -> dict[str, dict[str, str]]:
    # prevent any duplicate identifying value between default static roles from Tenzu and dynamic ones from Taiga
    old_to_new_mapping = {"slug": {}, "name": {}}
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
                        old_to_new_mapping[attribute][old_value] = new_value
                        role[attribute] = new_value
                        break
            else:
                old_to_new_mapping[attribute][old_value] = old_value
    return old_to_new_mapping


async def get_template_from_taiga_project(
    taiga_project: FullTaigaProjectImport,
) -> tuple[ProjectTemplateModel, dict[str, dict[str, str]]]:
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
        del role["tenzu_id"]
    for swimlane in serialized_project["swimlanes"]:
        swimlane["slug"] = slugify(swimlane["name"])
        del swimlane["statuses"]
        del swimlane["tenzu_id"]
    for status, colour in zip(
        serialized_project["us_statuses"], ordered_colour_generator()
    ):
        # no strong need for clever colour correspondance, it's probably acceptable to lose the hex colour from taiga
        status["color"] = colour
        del status["wip_limit"]
        del status["is_archived"]
        del status["is_closed"]
        del status["slug"]
        del status["tenzu_ids"]

    roles_old_to_new_mapping = ensure_roles_unique_attributes(
        default_roles, serialized_project["roles"]
    )

    template: ProjectTemplateModel = ProjectTemplateModel.model_construct(
        roles=[*default_roles, *serialized_project["roles"]],
        workflows=serialized_project["swimlanes"] or default_template.workflows,
        workflow_statuses=serialized_project["us_statuses"],
    )
    return template, roles_old_to_new_mapping


async def sync_project_ids_to_taiga_import(
    taiga_project: FullTaigaProjectImport,
    workflows: list[Workflow],
    roles: list[ProjectRole],
    roles_old_to_new_slug_mapping: dict[str, str],
):
    # assign tenzu ids to source objects from taiga project importation
    for role in taiga_project.roles or []:
        slug = roles_old_to_new_slug_mapping[role.slug]
        tenzu_role = next(filter(lambda r: r.slug == slug, roles))
        role.tenzu_id = tenzu_role.id
    for swimlane in taiga_project.swimlanes or []:
        tenzu_workflow = next(filter(lambda w: w.name == swimlane.name, workflows))
        swimlane.tenzu_id = tenzu_workflow.id
        statuses = list(tenzu_workflow.statuses.all())
        for status in swimlane.statuses or []:
            tenzu_status = next(filter(lambda s: s.name == status.status, statuses))
            status.tenzu_id = tenzu_status.id
    for status in taiga_project.us_statuses or []:
        tenzu_statuses_ids = [
            next(filter(lambda s: s.name == status.name, w.statuses.all())).id
            for w in workflows
        ]
        status.tenzu_ids = tenzu_statuses_ids


async def do_import_taiga_project(project_importation: ProjectImportation):
    with project_importation.source.open() as source_file:
        try:
            taiga_project = FullTaigaProjectImport.model_validate_json(
                source_file.read()
            )
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
        extra_fields = taiga_project.get_unknown_fields()
        if extra_fields:
            logger.warning(
                f"Project import {project_importation.id} for file '{Path(project_importation.source.name or '').name}' contains extra data: {extra_fields}"
            )

        await update_project_importation(
            project_importation, {"status": ImportationStatus.ONGOING}
        )
        template, roles_old_to_new_mapping = await get_template_from_taiga_project(
            taiga_project
        )
        project, roles = await projects_services._create_project(
            template=template,
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
        workflows = await workflows_services.list_workflows(project_id=project.id)
        await sync_project_ids_to_taiga_import(
            taiga_project, workflows, roles, roles_old_to_new_mapping["slug"]
        )
        # send small progress percentage to indicate creation of statuses, workflow and roles
        await update_project_importation(
            project_importation,
            {
                "project": project,
                "extra_data": {"progress_percentage": 2},
            },
        )
        pending_invites: dict[
            EmailStr, ProjectImportationPendingInvitation
        ] = await do_import_taiga_users(
            project_importation, taiga_project, roles, roles_old_to_new_mapping["name"]
        )

        if not taiga_project.is_kanban_activated:
            await update_project_importation(
                project_importation,
                {
                    "pending_invites": pending_invites,
                    "extra_data": {"progress_percentage": 100},
                },
            )
            await close_importation(project_importation)
            return
        # send small progress percentage to indicate creation of pending invitations
        await update_project_importation(
            project_importation,
            {
                "pending_invites": pending_invites,
                "extra_data": {"progress_percentage": 5},
            },
        )
        await do_import_taiga_stories(
            project_importation, workflows, taiga_project, pending_invites
        )
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
    await close_importation(project_importation)


async def close_importation(
    project_importation: ProjectImportation,
):
    if project_importation.pending_invites:
        await update_project_importation(
            project_importation,
            {
                "status": ImportationStatus.ACTION_NEEDED,
            },
        )
        await notifications.notify_when_project_importation_action_needed(
            project_importation
        )
    else:
        await succeed_project_importation(project_importation)


async def do_import_taiga_users(
    project_importation: ProjectImportation,
    taiga_project: FullTaigaProjectImport,
    roles: list[ProjectRole],
    roles_old_to_new_name_mapping: dict[str, str],
) -> dict[EmailStr, ProjectImportationPendingInvitation]:
    owner_role = next(filter(attrgetter("is_owner"), roles))

    def find_role(attribute: str, value: str) -> ProjectRole:
        return next(filter(lambda role: getattr(role, attribute) == value, roles))

    admin_role = find_role("slug", "admin")
    readonlymember_role = find_role("slug", "readonly-member")
    taiga_roles_mapping: dict[str, ProjectRole] = {
        old_name: find_role("name", new_name)
        for old_name, new_name in roles_old_to_new_name_mapping.items()
    }

    pending_invites: dict[EmailStr, ProjectImportationPendingInvitation] = {}
    if (
        taiga_project.owner is not None
        and taiga_project.owner != project_importation.created_by.email
    ):
        pending_invites[taiga_project.owner] = ProjectImportationPendingInvitation(
            role_id=owner_role.id,
            assigned_stories_ids=[],
            created_stories_ids=[],
            created_attachments_ids=[],
            created_comments_ids=[],
            deleted_comments_ids=[],
        )
    for membership in taiga_project.memberships or []:
        if membership.user is None or membership.user in (
            taiga_project.owner,
            project_importation.created_by.email,
        ):
            continue
        role_id = (
            admin_role.id
            if membership.is_admin
            else taiga_roles_mapping.get(membership.role, readonlymember_role).id
        )
        pending_invites[membership.user] = ProjectImportationPendingInvitation(
            role_id=role_id,
            assigned_stories_ids=[],
            created_stories_ids=[],
            created_attachments_ids=[],
            created_comments_ids=[],
            deleted_comments_ids=[],
        )
    return pending_invites


async def do_import_taiga_stories(
    project_importation: ProjectImportation,
    workflows: list[Workflow],
    taiga_project: FullTaigaProjectImport,
    pending_invites: dict[EmailStr, ProjectImportationPendingInvitation],
):
    processed_stories = 0
    total_stories = len(taiga_project.user_stories)
    current_percentage = project_importation.extra_data.get("progress_percentage", 0)
    workflow_ids_by_name: dict[str | None, tuple[UUID, dict[str, UUID]]] = {
        workflow.name: (
            workflow.id,
            {status.name: status.id for status in workflow.statuses.all()},
        )
        for workflow in workflows
    }
    workflow_ids_by_name[None] = next(
        iter(workflow_ids_by_name.values())
    )  # handle the case of no swimlane
    stories_to_create: list[Story] = []
    assignments_to_create: list[StoryAssignment] = []
    attachments_to_create: list[Attachment] = []
    comments_to_create: list[Comment] = []
    attachment_warnings: list[notifications.WarningFileTooBig] = []
    all_to_create = (
        stories_to_create,
        assignments_to_create,
        attachments_to_create,
        comments_to_create,
        attachment_warnings,
    )
    pending_data: ProjectImportationPendingData = {
        "assigned_stories": [],
        "created_stories": [],
        "created_attachments": [],
        "created_comments": [],
        "deleted_comments": [],
    }
    await sync_to_async(ContentType.objects.get_for_model)(
        Story
    )  # fill cache for later generic relation queries (e.g. Comment, Attachment)
    # Start Node.js process once
    async with BlockNoteConverter(source_format="md") as converter:
        for taiga_story in taiga_project.user_stories:
            if taiga_story.status is None:
                logger.warning(
                    f"Project import {project_importation.id} for file '{Path(project_importation.source.name or '').name}' has a story without status: #{taiga_story.ref} {taiga_story.subject}"
                )
                continue
            workflow_id, statuses = workflow_ids_by_name[taiga_story.swimlane]
            status_id = statuses[taiga_story.status]
            await do_import_taiga_single_story(
                taiga_story=taiga_story,
                project_importation=project_importation,
                converter=converter,
                workflow_id=workflow_id,
                status_id=status_id,
                stories_to_create=stories_to_create,
                assignments_to_create=assignments_to_create,
                attachments_to_create=attachments_to_create,
                comments_to_create=comments_to_create,
                attachment_warnings=attachment_warnings,
                pending_data=pending_data,
            )
            if any(
                len(list_to_create) >= _IMPORTATION_BULK_SIZE
                for list_to_create in all_to_create
            ):
                await bulk_create_all(
                    project_importation=project_importation,
                    stories_to_create=stories_to_create,
                    assignments_to_create=assignments_to_create,
                    attachments_to_create=attachments_to_create,
                    comments_to_create=comments_to_create,
                    attachment_warnings=attachment_warnings,
                    pending_invites=pending_invites,
                    pending_data=pending_data,
                )
                for list_to_create in all_to_create:
                    list_to_create.clear()
                for pending_list in pending_data.values():
                    pending_list.clear()
            processed_stories += 1
            percentage = round(processed_stories / total_stories * 100)
            # send update every 5% gain
            if percentage >= current_percentage + 5:
                current_percentage = percentage
                await update_project_importation(
                    project_importation,
                    {
                        "extra_data": {"progress_percentage": current_percentage},
                        "pending_invites": pending_invites,
                    },
                )

    # Flush remaining objects, possibly empty
    await bulk_create_all(
        project_importation=project_importation,
        stories_to_create=stories_to_create,
        assignments_to_create=assignments_to_create,
        attachments_to_create=attachments_to_create,
        comments_to_create=comments_to_create,
        attachment_warnings=attachment_warnings,
        pending_invites=pending_invites,
        pending_data=pending_data,
    )
    await update_project_importation(
        project_importation,
        {
            "extra_data": {"progress_percentage": 100},
            "pending_invites": pending_invites,
        },
    )


async def do_import_taiga_single_story(
    taiga_story: _TaigaUserStory,
    project_importation: ProjectImportation,
    converter: BlockNoteConverter,
    workflow_id: UUID,
    status_id: UUID,
    stories_to_create: list[Story],
    assignments_to_create: list[StoryAssignment],
    attachments_to_create: list[Attachment],
    comments_to_create: list[Comment],
    attachment_warnings: list[notifications.WarningFileTooBig],
    pending_data: ProjectImportationPendingData,
):
    assigned_users: set[EmailStr | None] = {
        taiga_story.assigned_to,
        *taiga_story.assigned_users,
    }
    assigned_users.discard(None)
    assigned_users: set[EmailStr]
    creator = (
        project_importation.created_by
        if project_importation.created_by.email == taiga_story.owner
        else None
    )

    binary_data, block_data = None, None
    if taiga_story.description:
        _, binary_data, block_data = await converter.convert(
            {"id": "0", "content": taiga_story.description}
        )

    story = Story(
        title=taiga_story.subject,
        description=block_data,
        description_binary=binary_data,
        project_id=project_importation.project_id,
        workflow_id=workflow_id,
        status_id=status_id,
        created_by=creator,
        order=taiga_story.kanban_order,
        created_at=taiga_story.created_date,
        description_updated_at=taiga_story.modified_date,
        version=taiga_story.version,
    )
    if taiga_story.owner is not None and story.created_by is None:
        pending_data["created_stories"].append(
            ProjectImportationPendingObject(
                user_email=taiga_story.owner, db_object=story
            )
        )
    stories_to_create.append(story)
    if project_importation.created_by.email in assigned_users:
        assignments_to_create.append(
            StoryAssignment(story=story, user=project_importation.created_by)
        )
        assigned_users.discard(project_importation.created_by.email)
    pending_data["assigned_stories"].extend(
        ProjectImportationPendingObject(user_email=user_email, db_object=story)
        for user_email in assigned_users
    )
    for taiga_attachment in sorted(taiga_story.attachments, key=attrgetter("order")):
        attachment = build_story_attachment_from_taiga(
            project_importation, story, taiga_attachment, attachment_warnings
        )
        if attachment is not None:
            attachments_to_create.append(attachment)
            if taiga_attachment.owner is not None and attachment.created_by is None:
                pending_data["created_attachments"].append(
                    ProjectImportationPendingObject(
                        user_email=taiga_attachment.owner, db_object=attachment
                    )
                )
    for event in taiga_story.history:
        (
            comment,
            comment_creator,
            comment_deleter,
        ) = await build_story_comment_from_taiga(
            converter,
            project_importation,
            story,
            event,
        )
        if comment is not None:
            comments_to_create.append(comment)
            if comment_creator is not None and comment.created_by is None:
                pending_data["created_comments"].append(
                    ProjectImportationPendingObject(
                        user_email=comment_creator, db_object=comment
                    )
                )
            if comment_deleter is not None and comment.deleted_by is None:
                pending_data["deleted_comments"].append(
                    ProjectImportationPendingObject(
                        user_email=comment_deleter, db_object=comment
                    )
                )


@transaction_atomic_async
async def bulk_create_all(
    project_importation: ProjectImportation,
    stories_to_create: list[Story],
    assignments_to_create: list[StoryAssignment],
    attachments_to_create: list[Attachment],
    comments_to_create: list[Comment],
    attachment_warnings: list[notifications.WarningFileTooBig],
    pending_invites: dict[EmailStr, ProjectImportationPendingInvitation],
    pending_data: ProjectImportationPendingData,
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
    # ids of objects should have been filled by now
    for pending_type, pending_list in pending_data.items():
        for pending_object in pending_list:
            try:
                pending_invite = pending_invites[pending_object["user_email"]]
            except KeyError:
                logger.warning(
                    f"Project import {project_importation.id} for file '{Path(project_importation.source.name or '').name}': Can't find user {pending_object['user_email']} in pending_invites_map"
                )
                pass
            else:
                pending_invite[f"{pending_type}_ids"].append(
                    pending_object["db_object"].id
                )


def build_story_attachment_from_taiga(
    project_importation: ProjectImportation,
    story: Story,
    attachment: _TaigaAttachment,
    attachment_warnings: list[notifications.WarningFileTooBig],
) -> Attachment | None:
    if attachment.attached_file is None:
        return None
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

    return Attachment(
        storaged_object=StoragedObject(file=file),
        name=file.name or "unknown",
        size=file.size,
        content_type=file.content_type,
        content_object=story,
        created_by=user,
    )


async def build_story_comment_from_taiga(
    converter: BlockNoteConverter,
    project_importation: ProjectImportation,
    story: Story,
    event: _TaigaHistory,
) -> tuple[Comment | None, EmailStr | None, EmailStr | None]:
    if not event.comment:
        return None, None, None
    creator_email = event.user[0] if event.user else None
    user = (
        project_importation.created_by
        if project_importation.created_by.email == creator_email
        else None
    )
    deleter_email = (
        event.delete_comment_user[0]
        if (event.delete_comment_user and event.delete_comment_date)
        else None
    )
    delete_comment_user = (
        project_importation.created_by
        if project_importation.created_by.email == deleter_email
        else None
    )

    block_data = ""
    if not event.delete_comment_date:
        _, _, block_data = await converter.convert(
            {"id": "0", "content": event.comment}
        )
    return (
        Comment(
            content_object=story,
            text=block_data,
            created_at=event.created_at,
            created_by=user,
            deleted_at=event.delete_comment_date,
            deleted_by=delete_comment_user,
            modified_at=event.edit_comment_date,
        ),
        creator_email,
        deleter_email,
    )
