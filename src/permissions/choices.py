# -*- coding: utf-8 -*-
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

from base.db.models import TextChoices


class EditStoryPermissions(TextChoices):
    ADD_STORY = "add_story", "Add story"
    COMMENT_STORY = "comment_story", "Comment story"
    DELETE_STORY = "delete_story", "Delete story"
    MODIFY_STORY = "modify_story", "Modify story"


# possible permissions for members or public members
# directly applied to default "general" project role
# these may be changed by a project admin
# also, permissions for ws-admins
class ProjectPermissions(TextChoices):
    # Story permissions
    ADD_STORY = "add_story", "Add story"
    COMMENT_STORY = "comment_story", "Comment story"
    DELETE_STORY = "delete_story", "Delete story"
    MODIFY_STORY = "modify_story", "Modify story"
    VIEW_STORY = "view_story", "View story"


# possible permissions for workspace members
# these may be changed by a workspace admin
class WorkspacePermissions(TextChoices):
    # Global permissions
    VIEW_WORKSPACE = "view_workspace", "View workspace"
