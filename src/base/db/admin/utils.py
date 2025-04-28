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
from django.contrib.contenttypes.models import ContentType
from django.db.models import Model
from django.urls import reverse
from django.utils.html import format_html


def linkify(object: Model, field_name: str) -> str:
    """
    Get an object and a field_name of a ForeignKey or GenericForeignKey field and return a link to the related object.
    """
    linked_obj = getattr(object, field_name)
    linked_content_type = ContentType.objects.get_for_model(linked_obj)
    app_label = linked_content_type.app_label
    model_name = linked_content_type.model
    view_name = f"admin:{app_label}_{model_name}_change"
    link_url = reverse(view_name, args=[linked_obj.pk])
    return format_html('<a href="{}">{}</a>', link_url, linked_obj)
