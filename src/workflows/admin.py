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

from base.db import admin
from projects.projects.models import Project
from workflows.models import Workflow, WorkflowStatus


class WorkflowStatusInline(admin.TabularInline):
    model = WorkflowStatus
    extra = 0


@admin.register(Workflow)
class WorkflowAdmin(admin.ModelAdmin):
    fieldsets = ((None, {"fields": ("id", "name", "slug", "order", "project")}),)
    readonly_fields = [
        "id",
        # "created_at", "modified_at"
    ]
    list_display = ["name", "project", "slug", "order"]
    search_fields = ["id", "name", "slug", "project__name"]
    ordering = (
        "project__name",
        "order",
        "name",
    )
    inlines = [WorkflowStatusInline]


class WorkflowInline(admin.TabularInline):
    model = Workflow
    extra = 0
