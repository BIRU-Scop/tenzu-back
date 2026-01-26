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

import json
import logging
import subprocess

from django.conf import settings

from stories.stories.models import Story

logger = logging.getLogger(__name__)


def migrate_story_in_batches(StoryClass: type[Story]):
    script_path = settings.BASE_DIR / "scripts" / "convert_blocknote.mjs"

    # Start Node.js process once
    process = subprocess.Popen(
        ["node", "--max-old-space-size=4096", script_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,  # Line buffered
    )

    BULK_SIZE = 250

    try:
        stories_to_process = (
            StoryClass.objects.exclude(description__isnull=True)
            .exclude(description="")
            .only("id", "description")
        )
        total = stories_to_process.count()
        print(f"\nStarting batch migration of {total} stories...")

        processed_count = 0
        pending_updates: list[Story] = []

        for story in stories_to_process:
            # Check if the process is still active
            if process.poll() is not None:
                stderr_data = process.stderr.read()
                raise RuntimeError(
                    f"Node.js process terminated unexpectedly with code {process.returncode}. Error: {stderr_data}"
                )

            # Send one story as a JSON line to Node
            input_data = json.dumps(
                {"id": str(story.id), "description": story.description}
            )
            try:
                process.stdin.write(input_data + "\n")
                process.stdin.flush()
            except BrokenPipeError:
                stderr_data = process.stderr.read()
                raise RuntimeError(
                    f"Broken pipe: Node.js crashed. Details: {stderr_data}"
                )

            # Read the result (one line)
            line = process.stdout.readline()
            if line:
                story_id_str, hex_data = line.strip().split(":", 1)

                if hex_data in {"ERROR", "EMPTY"}:
                    logger.error(
                        f"Error or empty description for story ID: {story_id_str}"
                    )
                    processed_count += 1
                    continue

                binary_data = bytes.fromhex(hex_data)

                # Accumulate updates for bulk_update
                pending_updates.append(
                    StoryClass(id=story_id_str, description_binary=binary_data)
                )

                if len(pending_updates) >= BULK_SIZE:
                    StoryClass.objects.bulk_update(
                        pending_updates,
                        ["description_binary"],
                        batch_size=BULK_SIZE,
                    )
                    pending_updates.clear()

            processed_count += 1
            if processed_count % 100 == 0:
                print(f"Progress: {processed_count}/{total}")

        # Flush remaining updates
        if pending_updates:
            StoryClass.objects.bulk_update(
                pending_updates,
                ["description_binary"],
                batch_size=BULK_SIZE,
            )

    finally:
        if process.stdin:
            process.stdin.close()
        process.terminate()
        process.wait()
