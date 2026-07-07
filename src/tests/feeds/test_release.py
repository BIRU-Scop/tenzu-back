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

import ast
from datetime import timedelta

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from feeds.management.commands.create_release_feeditem import (
    build_migration_source,
    next_migration_name,
)
from feeds.migrations._data import apply_release
from feeds.models import FeedItem, FeedItemType
from ninja_jwt.utils import aware_utcnow
from tests.utils import factories as f

##########################################################
# apply_release (data logic, tested without a migration)
##########################################################


@pytest.mark.django_db
def test_apply_release_creates_new_and_closes_previous(empty_feed_items):
    now = aware_utcnow()
    previous = f.FeedItemFactory.create(
        type=FeedItemType.RELEASE,
        publication_date=now - timedelta(days=10),
        expiration_date=None,
    )

    created = apply_release(
        FeedItem, title="Version 2", content="# Notes\n\nSome **markdown**.", now=now
    )

    previous.refresh_from_db()
    assert previous.expiration_date == now
    assert created.type == FeedItemType.RELEASE
    assert created.title == "Version 2"
    assert created.content == "# Notes\n\nSome **markdown**."
    assert created.publication_date == now
    assert created.expiration_date is None
    # The "single active release" invariant holds.
    active = FeedItem.objects.filter(
        type=FeedItemType.RELEASE, active_period__upper_inf=True
    ).count()
    assert active == 1


##########################################################
# build_migration_source (pure codegen)
##########################################################


def test_build_migration_source_is_valid_and_roundtrips_adversarial_content():
    # Tricky content: triple-quotes, backslashes, braces, newlines.
    content = "Tricky \"\"\" ''' \\ {not_a_field} content\nsecond line"
    source = build_migration_source(
        title="My Release",
        content=content,
        dependency="0001_initial",
        action_title="",
        action_url="",
    )

    # Syntactically valid.
    ast.parse(source)

    # Executable and round-trips identically.
    namespace: dict = {}
    exec(compile(source, "<generated>", "exec"), namespace)
    assert namespace["CONTENT"] == content
    assert namespace["TITLE"] == "My Release"
    assert namespace["Migration"].dependencies == [("feeds", "0001_initial")]


def test_next_migration_name_increments_and_slugifies():
    name = next_migration_name("0007_something", "Version 2.0 !")
    assert name.startswith("0008_release_")


##########################################################
# Command: title validation
##########################################################


def test_command_rejects_title_longer_than_50(tmp_path):
    markdown = tmp_path / "notes.md"
    markdown.write_text("# Notes", encoding="utf-8")

    with pytest.raises(CommandError):
        call_command("create_release_feeditem", str(markdown), title="x" * 51)


def test_command_rejects_missing_markdown_file(tmp_path):
    with pytest.raises(CommandError):
        call_command(
            "create_release_feeditem",
            str(tmp_path / "does_not_exist.md"),
            title="Release",
        )
