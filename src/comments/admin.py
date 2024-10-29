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
from base.db.admin.utils import linkify
from comments.models import Comment


class _CalculatedCommentAttrsMixin:
    @admin.display(boolean=True)
    def was_modified(self, obj: Comment) -> bool:
        return bool(obj.modified_at)

    @admin.display(boolean=True)
    def was_deleted(self, obj: Comment) -> bool:
        return bool(obj.deleted_at)

    @admin.display(description="Related to object")
    def content_object_link(self, obj: Comment) -> str:
        return linkify(object=obj, field_name="content_object")


class CommentInline(_CalculatedCommentAttrsMixin, admin.GenericTabularInline):
    model = Comment
    ct_field = "object_content_type"
    ct_fk_field = "object_id"
    fields = (
        "b64id",
        "text",
        "created_at",
        "created_by",
        "was_modified",
        "was_deleted",
    )
    readonly_fields = (
        "b64id",
        "created_at",
        "created_by",
        "was_modified",
        "was_deleted",
    )
    show_change_link = True
    extra = 0


@admin.register(Comment)
class CommentAdmin(_CalculatedCommentAttrsMixin, admin.ModelAdmin):
    fieldsets = (
        (
            None,
            {
                "fields": (
                    ("id", "b64id"),
                    "text",
                    ("created_at", "created_by"),
                    "modified_at",
                    ("deleted_at", "deleted_by"),
                    (
                        "object_content_type",
                        "object_id",
                    ),
                    "content_object_link",
                )
            },
        ),
    )
    readonly_fields = (
        "id",
        "b64id",
        "created_at",
        "created_by",
        "modified_at",
        "deleted_at",
        "deleted_by",
        "content_object_link",
    )
    list_display = (
        "b64id",
        "text",
        "created_by",
        "was_modified",
        "was_deleted",
        "content_object_link",
    )
    list_filter = ("created_by",)
    search_fields = (
        "id",
        "text",
        "object_id",
    )
    ordering = ("-created_at",)
