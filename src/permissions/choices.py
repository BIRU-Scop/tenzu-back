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
from typing import Self

from django.db.models import TextChoices
from django.db.models.enums import ChoicesType


class PermissionsBaseType(ChoicesType):
    """
    A metaclass for creating a permissions enum choices.
    Needed to hack around the restriction about inheriting from an enum and to actually inherit enum members
    """

    @classmethod
    def _check_for_existing_members_(metacls, name, bases):
        # prevent any class using this metaclass from being checked
        return super()._check_for_existing_members_(
            name, [b for b in bases if not isinstance(b, metacls)]
        )

    def __new__(metacls, name, bases, attrs, **kwargs):
        parents = [b for b in bases if isinstance(b, PermissionsBaseType)]
        if not parents:
            return super().__new__(metacls, name, bases, attrs, **kwargs)
        for parent in parents:
            attrs.update(
                {member.name: (member.value, member.label) for member in parent}
            )
        return super().__new__(metacls, name, bases, attrs, **kwargs)


class PermissionsBase(TextChoices, metaclass=PermissionsBaseType):
    """
    Common class used mainly for typing purposes
    """

    # Member permissions
    CREATE_MODIFY_MEMBER = "create_modify_member", "Create or modify a member"
    DELETE_MEMBER = "delete_member", "Delete a member"

    @classmethod
    def dependencies(cls) -> list[tuple[Self, Self]]:
        """
        List of dependency relations in format (permission, required_permission)
        """
        return [(cls.DELETE_MEMBER, cls.CREATE_MODIFY_MEMBER)]


class ProjectPermissions(PermissionsBase):
    """
    possible permissions for members
    directly applied to default project roles, editable roles may be changed
    """

    # Member permissions
    CREATE_MODIFY_DELETE_ROLE = (
        "create_modify_delete_role",
        "Create, modify or delete any editable role",
    )
    # Global permissions
    MODIFY_PROJECT = "modify_project", "Modify info of project"
    DELETE_PROJECT = "delete_project", "Delete the project"
    # Story permissions
    VIEW_STORY = "view_story", "View stories in project"
    MODIFY_STORY = "modify_story", "Modify the stories"
    CREATE_STORY = "create_story", "Create new stories"
    DELETE_STORY = "delete_story", "Delete existing stories"
    # Comment permissions
    VIEW_COMMENT = "view_comment", "View comments in stories"
    CREATE_MODIFY_DELETE_COMMENT = (
        "create_modify_delete_comment",
        "Post comment on stories, edit and delete own comments",
    )
    MODERATE_COMMENT = "moderate_comment", "Moderates other's comments"
    # Workflow module permissions
    VIEW_WORKFLOW = "view_workflow", "View workflows in project"
    MODIFY_WORKFLOW = "modify_workflow", "Modify the workflows"
    ADD_WORKFLOW = "add_workflow", "Create new workflows"
    DELETE_WORKFLOW = "delete_workflow", "Delete existing workflows"

    @classmethod
    def dependencies(cls) -> list[tuple[Self, Self]]:
        return super().dependencies() + [
            (
                cls.CREATE_MODIFY_DELETE_ROLE,
                cls.CREATE_MODIFY_MEMBER,
            ),
            (
                cls.DELETE_PROJECT,
                cls.MODIFY_PROJECT,
            ),
            (
                cls.MODIFY_STORY,
                cls.VIEW_STORY,
            ),
            (
                cls.CREATE_STORY,
                cls.MODIFY_STORY,
            ),
            (
                cls.DELETE_STORY,
                cls.CREATE_STORY,
            ),
            (
                cls.VIEW_COMMENT,
                cls.VIEW_STORY,
            ),
            (
                cls.CREATE_MODIFY_DELETE_COMMENT,
                cls.VIEW_COMMENT,
            ),
            (
                cls.MODERATE_COMMENT,
                cls.CREATE_MODIFY_DELETE_COMMENT,
            ),
            (
                cls.VIEW_WORKFLOW,
                cls.VIEW_STORY,
            ),
            (
                cls.MODIFY_WORKFLOW,
                cls.VIEW_WORKFLOW,
            ),
            (
                cls.ADD_WORKFLOW,
                cls.MODIFY_WORKFLOW,
            ),
            (
                cls.DELETE_WORKFLOW,
                cls.ADD_WORKFLOW,
            ),
        ]


class WorkspacePermissions(PermissionsBase):
    """
    possible permissions for workspace members
    the associated roles are a definite set
    """

    # Global permissions
    MODIFY_WORKSPACE = "modify_workspace", "Modify info of workspace"
    DELETE_WORKSPACE = "delete_workspace", "Delete the workspace"
    CREATE_PROJECT = "create_project", "Create project in workspace"

    @classmethod
    def dependencies(cls) -> list[tuple[Self, Self]]:
        return super().dependencies() + [
            (
                cls.DELETE_WORKSPACE,
                cls.MODIFY_WORKSPACE,
            )
        ]
