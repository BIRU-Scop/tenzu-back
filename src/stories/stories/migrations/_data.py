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

import logging
import subprocess

from django.conf import settings

from stories.stories.models import Story
from stories.stories.services.blocknote import (
    BlockNoteConverter,
    BlockNoteScriptError,
)

logger = logging.getLogger(__name__)


async def migrate_story_in_batches(StoryClass: type[Story]):
    BULK_SIZE = 250
    # Start Node.js process once
    async with BlockNoteConverter() as converter:
        stories_to_process = (
            StoryClass.objects.exclude(description__isnull=True)
            .exclude(description="")
            .only("id", "description")
        )
        total = await stories_to_process.acount()
        print(f"\nStarting batch migration of {total} stories...")

        processed_count = 0
        pending_updates: list[Story] = []

        async for story in stories_to_process:
            if processed_count % 100 == 0:
                print(f"Progress: {processed_count}/{total}")

            try:
                story_id_str, binary_data, _ = await converter.convert(
                    {"id": str(story.id), "content": story.description}
                )
            except BlockNoteScriptError:
                logger.error(f"Error or empty content for story with ID: {story.id}")
                processed_count += 1
                continue

            # Accumulate updates for bulk_update
            pending_updates.append(
                StoryClass(id=story_id_str, description_binary=binary_data)
            )

            if len(pending_updates) >= BULK_SIZE:
                await StoryClass.objects.abulk_update(
                    pending_updates,
                    ["description_binary"],
                    batch_size=BULK_SIZE,
                )
                pending_updates.clear()
            processed_count += 1

        # Flush remaining updates
        if pending_updates:
            await StoryClass.objects.abulk_update(
                pending_updates,
                ["description_binary"],
                batch_size=BULK_SIZE,
            )
        print(f"Progress: {processed_count}/{total}")
