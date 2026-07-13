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

import re
from pathlib import Path

from django.apps import apps
from django.core.management.base import BaseCommand, CommandError
from django.db.migrations.loader import MigrationLoader
from slugify import slugify

from feeds.models import FeedItem

_MIGRATION_BODY = """
from django.db import migrations
from django.utils import timezone

from feeds.migrations._data import apply_release

TITLE = {title!r}
CONTENT = {content!r}
ACTION_TITLE = {action_title!r}
ACTION_URL = {action_url!r}


def forwards(apps, schema_editor):
    # now = the migration's apply time (per instance); also closes
    # the previous active release.
    FeedItem = apps.get_model("feeds", "FeedItem")
    apply_release(FeedItem, title=TITLE, content=CONTENT, now=timezone.now(), action_title=ACTION_TITLE, action_url=ACTION_URL)


class Migration(migrations.Migration):
    dependencies = [("feeds", {dependency!r})]
    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
"""


def build_migration_source(
    *, title: str, content: str, action_title: str, action_url: str, dependency: str
) -> str:
    return _MIGRATION_BODY.format(
        title=title,
        content=content,
        action_title=action_title,
        action_url=action_url,
        dependency=dependency,
    )


def next_migration_name(leaf_name: str, title: str) -> str:
    match = re.match(r"^(\d+)", leaf_name)
    number = (int(match.group(1)) + 1) if match else 1
    slug = slugify(title, separator="_")
    return f"{number:04d}_release_{slug}"


class Command(BaseCommand):
    help = (
        "Generate a migration that creates a release FeedItem from a markdown "
        "file, closing the previous release."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "markdown_file",
            type=Path,
            help="Path to the markdown file holding the release content.",
        )
        parser.add_argument(
            "--title",
            required=True,
            help="Release title (max 50 characters).",
        )
        parser.add_argument(
            "--action_title",
            default="",
            help="Title for the optional CTA (max 30 characters).",
        )
        parser.add_argument(
            "--action_url",
            default="",
            help="URL of the action.",
        )

    def handle(self, *args, **options):
        title: str = options["title"]
        max_length = FeedItem._meta.get_field("title").max_length
        if len(title) > max_length:
            raise CommandError(f"Title exceeds {max_length} characters ({len(title)}).")

        path: Path = options["markdown_file"]
        try:
            content = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise CommandError(f"Cannot read {path}: {exc}")

        leaves = MigrationLoader(None, ignore_no_migrations=True).graph.leaf_nodes(
            "feeds"
        )
        if len(leaves) != 1:
            raise CommandError(
                "Expected exactly one leaf migration for the 'feeds' app, "
                f"found: {sorted(name for _, name in leaves)}."
            )
        leaf_name = leaves[0][1]

        name = next_migration_name(leaf_name, title)
        source = build_migration_source(
            title=title,
            content=content,
            action_title=options["action_title"],
            action_url=options["action_url"],
            dependency=leaf_name,
        )

        migrations_dir = Path(apps.get_app_config("feeds").path) / "migrations"
        target = migrations_dir / f"{name}.py"
        target.write_text(source, encoding="utf-8")

        self.stdout.write(self.style.SUCCESS(f"Migration generated: {target}"))
