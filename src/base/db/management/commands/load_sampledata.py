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
from asgiref.sync import async_to_sync
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import F

from base.sampledata.demo_data import load_demo_data
from base.sampledata.test_data import load_test_data
from projects.invitations.models import ProjectInvitation
from projects.memberships.models import ProjectMembership
from stories.stories.migrations._data import migrate_story_in_batches
from stories.stories.models import Story
from workspaces.invitations.models import WorkspaceInvitation


def sanity_check():
    """check for some invalid state in the app"""
    errors = []
    if (
        ProjectInvitation.objects.all()
        .filter(status="pending", user__project_memberships__project_id=F("project_id"))
        .exists()
    ):
        errors.append("Pending project invitation exists for members")
    if (
        WorkspaceInvitation.objects.all()
        .filter(
            status="pending",
            user__workspace_memberships__workspace_id=F("workspace_id"),
        )
        .exists()
    ):
        errors.append("Pending workspace invitation exists for members")
    if (
        ProjectMembership.objects.all()
        .exclude(user__workspace_memberships__workspace_id=F("project__workspace_id"))
        .exists()
    ):
        errors.append("Project memberships without corresponding workspace memberships")
    if errors:
        raise RuntimeError(errors)


class Command(BaseCommand):
    help = "Create all the test data"

    def add_arguments(self, parser):
        parser.add_argument("--no-test", action="store_true", help="Disable test data")
        parser.add_argument("--no-demo", action="store_true", help="Disable demo data")

    def handle(self, *args, **options):
        with transaction.atomic():
            if not options["no_test"]:
                async_to_sync(load_test_data)()
                sanity_check()
            if not options["no_demo"]:
                async_to_sync(load_demo_data)()
                sanity_check()
            migrate_story_in_batches(Story)
