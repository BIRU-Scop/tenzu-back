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

from typing import Any, Type

from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import Group
from django.http.request import HttpRequest

from base.db import admin
from base.db.admin import forms
from base.i18n import i18n
from projects.invitations.models import ProjectInvitation
from projects.memberships.models import ProjectMembership
from users.models import AuthData, User
from workspaces.memberships.models import WorkspaceMembership

admin.site.unregister(Group)


class ProjectInvitationInline(admin.TabularInline):
    model = ProjectInvitation
    fk_name = "user"
    fields = (
        "project",
        "role",
        "user",
        "email",
        "invited_by",
        "status",
        "num_emails_sent",
    )
    readonly_fields = ("project", "role", "user", "email", "invited_by")
    extra = 0

    def has_add_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False


class ProjectMembershipsInline(admin.TabularInline):
    model = ProjectMembership
    fields = ("project", "role")
    extra = 0

    def has_change_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False


class WorkspaceMembershipsInline(admin.TabularInline):
    model = WorkspaceMembership
    fields = ("workspace",)
    extra = 0

    def has_change_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False


class AuthDataInline(admin.TabularInline):
    model = AuthData
    extra = 0


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = (
        (None, {"fields": ("id", "username", "password")}),
        ("Personal info", {"fields": ("email", "full_name", "accepted_terms", "lang")}),
        ("Permissions", {"fields": ("is_active", "is_superuser")}),
        (
            "Important dates",
            {"fields": (("date_joined", "date_verification"), "last_login")},
        ),
    )
    readonly_fields = ("id", "date_joined", "date_verification", "last_login")
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "email", "full_name", "password1", "password2"),
            },
        ),
    )
    list_display = ("username", "email", "full_name", "is_active", "is_superuser")
    list_filter = ("is_superuser", "is_active")
    search_fields = ("username", "full_name", "email")
    ordering = ("username",)
    filter_horizontal = ()
    inlines = [
        AuthDataInline,
        WorkspaceMembershipsInline,
        ProjectMembershipsInline,
        ProjectInvitationInline,
    ]

    def get_form(
        self,
        request: HttpRequest,
        obj: User | None = None,
        change: bool = False,
        **kwargs: Any,
    ) -> Type[forms.ModelForm]:
        form = super().get_form(request, obj, **kwargs)

        if "lang" in form.base_fields:
            # Use Select widget to get a dynamic choices for lang field
            form.base_fields["lang"].widget = forms.widgets.Select(
                choices=(
                    (lang.code, lang.english_name)
                    for lang in i18n.available_languages_info
                )
            )

        return form
