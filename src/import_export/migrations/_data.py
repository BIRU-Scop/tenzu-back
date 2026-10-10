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
from uuid import UUID

from commons.utils.async_func import transaction_atomic_async
from commons.utils.colors import generate_random_color
from import_export.models import ImportationStatus, ProjectImportation
from import_export.serializers import FullTaigaProjectImport
from import_export.serializers.taiga import _TaigaStoryTag
from import_export.services.taiga import (
    backport_tenzu_ids_to_file,
    do_import_taiga_users,
    get_template_from_taiga_project,
)
from stories.tags.models import StoryTag, StoryTagAssignment


async def fill_pending_invites_for_importations_in_batches(
    ProjectImportationClass: type[ProjectImportation],
):
    BULK_SIZE = 250

    importations_to_process = (
        ProjectImportationClass.objects.exclude(status=ImportationStatus.FAILURE)
        .filter(project__isnull=False)
        .select_related("created_by")
        .prefetch_related("project__roles")
    )
    total = await importations_to_process.acount()
    print(f"\nStarting batch migration of {total} project importations...")

    processed_count = 0
    pending_updates: list[ProjectImportation] = []

    async for project_importation in importations_to_process:
        if processed_count % 100 == 0:
            print(f"Progress: {processed_count}/{total}")

        with project_importation.source.open() as source_file:
            taiga_project = FullTaigaProjectImport.model_validate_json(
                source_file.read()
            )
        template, roles_old_to_new_mapping = await get_template_from_taiga_project(
            taiga_project
        )

        project_importation.pending_invites = await do_import_taiga_users(
            project_importation=project_importation,
            taiga_project=taiga_project,
            roles=project_importation.project.roles.all(),
            roles_old_to_new_name_mapping=roles_old_to_new_mapping["name"],
        )
        if (
            project_importation.pending_invites
            and project_importation.status == ImportationStatus.SUCCESS
        ):
            project_importation.status = ImportationStatus.ACTION_NEEDED

        # Accumulate updates for bulk_update
        pending_updates.append(project_importation)

        if len(pending_updates) >= BULK_SIZE:
            await ProjectImportationClass.objects.abulk_update(
                pending_updates,
                ["status", "pending_invites"],
                batch_size=BULK_SIZE,
            )
            pending_updates.clear()
        processed_count += 1

    # Flush remaining updates
    if pending_updates:
        await ProjectImportationClass.objects.abulk_update(
            pending_updates,
            ["status", "pending_invites"],
            batch_size=BULK_SIZE,
        )
    print(f"Progress: {processed_count}/{total}")


async def fill_story_tags_for_importations_in_batches(
    ProjectImportationClass: type[ProjectImportation],
    StoryTagClass: type[StoryTag],
    StoryTagAssignmentClass: type[StoryTagAssignment],
):
    BULK_SIZE = 250

    importations_to_process = (
        ProjectImportationClass.objects.exclude(status=ImportationStatus.FAILURE)
        .filter(project__isnull=False)
        .exclude(project__story_tags__isnull=False)
        .select_related("created_by")
        .prefetch_related("project__roles")
    )
    total = await importations_to_process.acount()
    print(f"\nStarting batch migration of {total} project importations...")

    processed_count = 0

    async for project_importation in importations_to_process:
        tags_to_create: list[StoryTagClass] = []
        tag_assignments_to_create: list[StoryTagAssignmentClass] = []

        if processed_count % 100 == 0:
            print(f"Progress: {processed_count}/{total}")

        with project_importation.source.open() as source_file:
            taiga_project = FullTaigaProjectImport.model_validate_json(
                source_file.read()
            )
        project_story_tags: dict[str, StoryTag] = {}

        async with transaction_atomic_async():
            for taiga_story in taiga_project.user_stories:
                if taiga_story.tags:
                    if isinstance(taiga_story.tags[0], _TaigaStoryTag):
                        taiga_story.tags = [tag.label for tag in taiga_story.tags]
                    tags_to_create.extend(
                        [
                            StoryTagClass(
                                label=tag,
                                color=generate_random_color(),
                                project_id=project_importation.project_id,
                            )
                            for tag in taiga_story.tags
                            if project_story_tags.get(tag, None) is None
                        ]
                    )
                    project_story_tags.update(
                        {tag.label: tag for tag in tags_to_create}
                    )
                    assignments = [
                        StoryTagAssignmentClass(
                            tag=project_story_tags[tag], story_id=taiga_story.tenzu_id
                        )
                        for tag in taiga_story.tags
                    ]
                    tag_assignments_to_create.extend(assignments)
                    taiga_story.tags = [
                        _TaigaStoryTag(
                            label=assignment.tag.label, tenzu_id=assignment.tag_id
                        )
                        for assignment in assignments
                    ]

                if (
                    len(tags_to_create) > BULK_SIZE
                    or len(tag_assignments_to_create) > BULK_SIZE
                ):
                    await StoryTagClass.objects.abulk_create(tags_to_create)
                    await StoryTagAssignmentClass.objects.abulk_create(
                        tag_assignments_to_create
                    )
                    tags_to_create.clear()
                    tag_assignments_to_create.clear()

            # Flush remaining updates
            if tags_to_create:
                await StoryTagClass.objects.abulk_create(tags_to_create)
            if tag_assignments_to_create:
                await StoryTagAssignmentClass.objects.abulk_create(
                    tag_assignments_to_create
                )
            del project_importation.source.file
            with project_importation.source.open(mode="w") as source_file:
                source_file.write(
                    taiga_project.model_dump_json(
                        exclude_unset=True, round_trip=True, warnings="error"
                    )
                )
        processed_count += 1

    print(f"Progress: {processed_count}/{total}")
