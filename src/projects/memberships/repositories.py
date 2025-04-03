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


from memberships.repositories import (  # noqa
    delete_membership,
    get_membership,
    get_role,
    list_memberships,
    list_roles,
    update_membership,
    update_role,
)
from projects.memberships.models import ProjectMembership, ProjectRole
from projects.projects.models import Project
from users.models import User

##########################################################
# create project membership
##########################################################


async def create_project_membership(
    user: User, project: Project, role: ProjectRole
) -> ProjectMembership:
    return await ProjectMembership.objects.acreate(
        user=user, project=project, role=role
    )


##########################################################
# create project role
##########################################################


async def create_project_role(
    name: str,
    slug: str,
    permissions: list[str],
    is_owner: bool,
    editable: bool,
    project: Project,
    order: int | None = None,
) -> ProjectRole:
    return await ProjectRole.objects.acreate(
        name=name,
        slug=slug,
        permissions=permissions,
        is_owner=is_owner,
        editable=editable,
        project=project,
        order=order,
    )


##########################################################
# misc
##########################################################


async def list_project_members(project: Project, exclude_user=None) -> list[User]:
    qs = project.members.all()
    if exclude_user is not None:
        qs = qs.exclude(id=exclude_user.id)
    return [a async for a in qs]
