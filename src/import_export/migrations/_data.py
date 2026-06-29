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

from import_export.models import ImportationStatus, ProjectImportation
from import_export.serializers import TaigaProjectImport
from import_export.services.taiga import (
    do_import_taiga_users,
    get_template_from_taiga_project,
)


async def fill_pending_invites_for_importations_in_batches(
    ProjectImportationClass: type[ProjectImportation],
):
    BULK_SIZE = 250

    importations_to_process = (
        ProjectImportationClass.objects.exclude(status=ImportationStatus.FAILURE)
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
            taiga_project = TaigaProjectImport.model_validate_json(source_file.read())
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
