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
from django.db.models import Count, QuerySet
from django.http.request import HttpRequest

from base.db import admin
from comments.admin import CommentInline
from mediafiles.admin import MediafileInline
from stories.stories.models import Story


@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "id",
                    "ref",
                    "title",
                    "description",
                    "order",
                    "project",
                    "workflow",
                    "status",
                )
            },
        ),
        (
            "Extra info",
            {
                "classes": ("collapse",),
                "fields": (
                    "created_by",
                    "created_at",
                    "title_updated_by",
                    "title_updated_at",
                    "description_updated_by",
                    "description_updated_at",
                ),
            },
        ),
    )
    readonly_fields = (
        "id",
        "ref",
        "created_by",
        "created_at",
        "title_updated_by",
        "title_updated_at",
        "description_updated_by",
        "description_updated_at",
    )
    list_display = [
        "ref",
        "title",
        "project",
        "workflow",
        "status",
        "order",
        "total_mediafiles",
        "total_comments",
    ]
    list_filter = ("project", "created_by")
    search_fields = [
        "id",
        "ref",
        "title",
        "description",
        "project__name",
        "workflow__name",
    ]
    ordering = ("project__name", "workflow__order", "status__order", "order")
    inlines = [
        MediafileInline,
        CommentInline,
    ]

    def get_queryset(self, request: HttpRequest) -> QuerySet[Story]:
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            comments_count=Count("comments"),
            mediafiles_count=Count("mediafiles"),
        )
        return queryset

    @admin.display(description="# comments", ordering="comments_count")
    def total_comments(self, obj: Story) -> int:
        return obj.comments_count  # type: ignore[attr-defined]

    @admin.display(description="# mediafiles", ordering="mediafiles_count")
    def total_mediafiles(self, obj: Story) -> int:
        return obj.mediafiles_count  # type: ignore[attr-defined]
