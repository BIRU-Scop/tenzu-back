# Copyright (C) 2024 BIRU
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

from django.conf import settings
from django.utils.text import capfirst

from permissions.choices import ProjectPermissions


def create_initial_project_template(apps, schema_editor):
    ProjectTemplate = apps.get_model("projects", "ProjectTemplate")

    ProjectTemplate.objects.create(
        id=UUID("00000000-0000-0000-0000-000000000001"),
        name=capfirst(settings.DEFAULT_PROJECT_TEMPLATE),
        slug=settings.DEFAULT_PROJECT_TEMPLATE,
        roles=[
            {
                "slug": "owner",
                "name": "Owner",
                "editable": False,
                "order": 1,
                "is_owner": True,
                "permissions": list(ProjectPermissions.values),
            },
            {
                "slug": "admin",
                "name": "Admin",
                "editable": False,
                "order": 2,
                "is_owner": False,
                "permissions": [
                    ProjectPermissions.CREATE_MODIFY_MEMBER.value,
                    ProjectPermissions.DELETE_MEMBER.value,
                    ProjectPermissions.CREATE_MODIFY_DELETE_ROLE.value,
                    ProjectPermissions.MODIFY_PROJECT.value,
                    ProjectPermissions.VIEW_STORY.value,
                    ProjectPermissions.MODIFY_STORY.value,
                    ProjectPermissions.CREATE_STORY.value,
                    ProjectPermissions.DELETE_STORY.value,
                    ProjectPermissions.VIEW_COMMENT.value,
                    ProjectPermissions.CREATE_MODIFY_DELETE_COMMENT.value,
                    ProjectPermissions.MODERATE_COMMENT.value,
                    ProjectPermissions.VIEW_WORKFLOW.value,
                    ProjectPermissions.MODIFY_WORKFLOW.value,
                    ProjectPermissions.ADD_WORKFLOW.value,
                    ProjectPermissions.DELETE_WORKFLOW.value,
                ],
            },
            {
                "slug": "readonly-member",
                "name": "Readonly-member",
                "editable": False,
                "order": 3,
                "is_owner": False,
                "permissions": [
                    ProjectPermissions.VIEW_STORY.value,
                    ProjectPermissions.VIEW_COMMENT.value,
                    ProjectPermissions.VIEW_WORKFLOW.value,
                ],
            },
            {
                "slug": "member",
                "name": "Member",
                "editable": True,
                "order": 4,
                "is_owner": False,
                "permissions": [
                    ProjectPermissions.VIEW_STORY.value,
                    ProjectPermissions.MODIFY_STORY.value,
                    ProjectPermissions.CREATE_STORY.value,
                    ProjectPermissions.DELETE_STORY.value,
                    ProjectPermissions.VIEW_COMMENT.value,
                    ProjectPermissions.CREATE_MODIFY_DELETE_COMMENT.value,
                    ProjectPermissions.VIEW_WORKFLOW.value,
                    ProjectPermissions.MODIFY_WORKFLOW.value,
                    ProjectPermissions.ADD_WORKFLOW.value,
                    ProjectPermissions.DELETE_WORKFLOW.value,
                ],
            },
        ],
        workflows=[{"slug": "main", "name": "Main", "order": 1}],
        workflow_statuses=[
            {"name": "New", "order": 1, "color": 1},
            {"name": "Ready", "order": 2, "color": 2},
            {"name": "In progress", "order": 3, "color": 3},
            {"name": "Done", "order": 4, "color": 4},
        ],
    )
