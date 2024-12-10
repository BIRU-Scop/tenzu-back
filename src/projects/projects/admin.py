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

from typing import Any

from django.http.request import HttpRequest

from base.db import admin
from base.db.admin.forms import ModelChoiceField
from base.db.models import ForeignKey
from projects.invitations.models import ProjectInvitation
from projects.memberships.models import ProjectMembership
from projects.projects.models import Project, ProjectTemplate
from projects.roles.models import ProjectRole
from workflows.admin import WorkflowInline


class ProjectRoleInline(admin.TabularInline):
    model = ProjectRole
    fields = ("project", "name", "slug", "order", "is_admin", "permissions")
    extra = 0


class ProjectMembershipInline(admin.TabularInline):
    model = ProjectMembership
    fields = ("project", "role", "user")
    extra = 0

    def get_formset(
        self, request: HttpRequest, obj: Project | None = None, **kwargs: Any
    ) -> Any:
        self.parent_obj = obj  # Use in formfield_for_foreignkey()
        return super().get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(
        self, db_field: ForeignKey[Any, Any], request: HttpRequest, **kwargs: Any
    ) -> ModelChoiceField:
        if db_field.name in ["role"]:
            kwargs["queryset"] = db_field.related_model.objects.filter(
                project=self.parent_obj
            )

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class ProjectInvitationInline(admin.TabularInline):
    model = ProjectInvitation
    extra = 0

    def get_formset(
        self, request: HttpRequest, obj: Project | None = None, **kwargs: Any
    ) -> Any:
        self.parent_obj = obj  # Use in formfield_for_foreignkey()
        return super().get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(
        self, db_field: ForeignKey[Any, Any], request: HttpRequest, **kwargs: Any
    ) -> ModelChoiceField:
        if db_field.name in ["role"]:
            kwargs["queryset"] = db_field.related_model.objects.filter(
                project=self.parent_obj
            )

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {"fields": (("id", "b64id"), "workspace", "name", "created_by")}),
        (
            "Extra info",
            {
                "classes": ("collapse",),
                "fields": ("color", "logo", ("created_at", "modified_at")),
            },
        ),
        ("Permissions", {"fields": ("public_permissions",)}),
    )
    readonly_fields = ("id", "b64id", "created_at", "modified_at")
    list_display = [
        "b64id",
        "name",
        "workspace",
        "created_by",
        "public_user_can_view",
        "anon_user_can_view",
    ]
    list_filter = ("workspace", "created_by")
    search_fields = [
        "id",
        "name",
        "workspace__name",
    ]
    ordering = ("name",)
    inlines = [
        ProjectRoleInline,
        ProjectMembershipInline,
        ProjectInvitationInline,
        WorkflowInline,
    ]

    @admin.display(description="allow public users", boolean=True)
    def public_user_can_view(self, obj: Project) -> bool:
        return obj.public_user_can_view

    @admin.display(description="allow anonymous users", boolean=True)
    def anon_user_can_view(self, obj: Project) -> bool:
        return obj.anon_user_can_view


@admin.register(ProjectTemplate)
class ProjectTemplateAdmin(admin.ModelAdmin):
    pass
