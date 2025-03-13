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

from django.db.models import ForeignKey, QuerySet
from django.http.request import HttpRequest

from base.db import admin
from base.db.admin.forms import ModelChoiceField
from users.models import User
from workspaces.invitations.models import WorkspaceInvitation
from workspaces.memberships.models import WorkspaceMembership
from workspaces.workspaces.models import Workspace


class WorkspaceMembershipInline(admin.TabularInline):
    model = WorkspaceMembership
    extra = 0

    def get_formset(
        self, request: HttpRequest, obj: Workspace | None = None, **kwargs: Any
    ) -> Any:
        self.parent_obj = obj  # Use in formfield_for_foreignkey()
        return super().get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(
        self, db_field: ForeignKey[Any, Any], request: HttpRequest, **kwargs: Any
    ) -> ModelChoiceField:
        if db_field.name in ["role"]:
            kwargs["queryset"] = db_field.related_model.objects.filter(
                workspace=self.parent_obj
            )

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class WorkspaceGuestsInline(admin.NonrelatedTabularInline):
    model = User
    fields = ["username", "full_name", "list_projects"]
    extra = 0
    readonly_fields = (
        "username",
        "full_name",
        "list_projects",
    )
    verbose_name = "Workspace guest"

    def list_projects(self, obj: User) -> list[str]:
        return list(
            obj.projects.filter(workspace=self.parent_obj).values_list(
                "name", flat=True
            )
        )

    def get_form_queryset(self, obj: Workspace | None = None) -> QuerySet[User]:
        if not obj:
            return self.model.objects.none()
        self.parent_obj = obj  # Use in list_projects
        qs = self.model.objects.exclude(workspaces=self.parent_obj)
        qs = qs.filter(projects__workspace=self.parent_obj).distinct()
        return qs

    # This will help you to disbale add functionality
    def has_add_permission(self, request: HttpRequest, obj: User | None = None) -> bool:
        return False

    # This will help you to disable delete functionaliyt
    def has_delete_permission(
        self, request: HttpRequest, obj: User | None = None
    ) -> bool:
        return False


class WorkspaceInvitationInline(admin.TabularInline):
    model = WorkspaceInvitation
    extra = 0

    def get_formset(
        self, request: HttpRequest, obj: Workspace | None = None, **kwargs: Any
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


@admin.register(Workspace)
class WorkspaceAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {"fields": (("id", "b64id"), "name", "created_by")}),
        (
            "Extra info",
            {
                "classes": ("collapse",),
                "fields": ("color", ("created_at", "modified_at")),
            },
        ),
    )
    readonly_fields = ("id", "b64id", "created_at", "modified_at")
    list_display = ["b64id", "name", "created_by"]
    list_filter = ["created_by"]
    search_fields = ["id", "name"]
    ordering = ("name",)
    inlines = [
        WorkspaceMembershipInline,
        WorkspaceInvitationInline,
        WorkspaceGuestsInline,
    ]
