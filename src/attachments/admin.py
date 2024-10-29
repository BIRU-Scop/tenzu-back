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

from attachments.models import Attachment
from base.db import admin
from base.db.admin.utils import linkify


class AttachmentInline(admin.GenericTabularInline):
    model = Attachment
    ct_field = "object_content_type"
    ct_fk_field = "object_id"
    fields = ("name", "storaged_object", "content_type", "size")
    readonly_fields = ("name", "storaged_object", "content_type", "size")
    show_change_link = True

    def has_change_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False

    def has_add_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    fieldsets = (
        (
            None,
            {
                "fields": (
                    ("id", "b64id"),
                    ("name", "size", "content_type"),
                    "storaged_object",
                    ("created_at", "created_by"),
                    ("object_content_type", "object_id"),
                    "content_object_link",
                )
            },
        ),
    )
    list_display = (
        "b64id",
        "name",
        "content_object_link",
        "created_by",
    )
    readonly_fields = (
        "id",
        "b64id",
        "created_at",
        "created_by",
        "content_object_link",
    )
    search_fields = (
        "name",
        "content_type",
    )
    list_filter = ("object_content_type",)
    ordering = ("-created_at",)

    @admin.display(description="Related to object")
    def content_object_link(self, obj: Attachment) -> str:
        return linkify(object=obj, field_name="content_object")
