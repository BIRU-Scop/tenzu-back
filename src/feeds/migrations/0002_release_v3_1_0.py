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

from django.db import migrations
from django.utils import timezone

from feeds.migrations._data import apply_release

TITLE = "v3.1.0"
CONTENT = "- News feed API: send news to your users directly from a pop-up in Tenzu! New releases will be shown that way, just like what you're reading right now ;)\n- Users importation from Taiga: when you import a project from Taiga, you can now automatically invite back any previous members\n"
ACTION_TITLE = "Read the article"
ACTION_URL = "https://tenzu.net/blog/logbook-12-users-taiga-news-feed"


def forwards(apps, schema_editor):
    # now = the migration's apply time (per instance); also closes
    # the previous active release.
    FeedItem = apps.get_model("feeds", "FeedItem")
    apply_release(
        FeedItem,
        title=TITLE,
        content=CONTENT,
        now=timezone.now(),
        action_title=ACTION_TITLE,
        action_url=ACTION_URL,
    )


class Migration(migrations.Migration):
    dependencies = [("feeds", "0001_initial")]
    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
