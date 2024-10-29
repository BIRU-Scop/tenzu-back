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
from mediafiles.models import Mediafile


class MediafileInline(admin.GenericTabularInline):
    model = Mediafile
    ct_field = "object_content_type"
    ct_fk_field = "object_id"
    fields = ("name", "file", "content_type", "size")
    readonly_fields = ("name", "file", "content_type", "size")
    show_change_link = True

    def has_change_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False

    def has_add_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False


@admin.register(Mediafile)
class StoryAdmin(admin.ModelAdmin):
    list_filter = ("project", "object_content_type")
    list_display = (
        "name",
        "project",
        "content_object",
        "object_content_type",
    )
    search_fields = (
        "name",
        "content_type",
    )
