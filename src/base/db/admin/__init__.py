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


from django.contrib.admin import ModelAdmin as DjangoModelAdmin
from django.contrib.admin import StackedInline as DjangoStackedInline
from django.contrib.admin import TabularInline as DjangoTabularInline
from django.contrib.admin import display, register, site  # noqa
from django.contrib.contenttypes.admin import (  # noqa
    GenericStackedInline,
    GenericTabularInline,
)
from django.db.models import JSONField
from nonrelated_inlines.admin import NonrelatedTabularInline  # type: ignore  # noqa

from base.db.admin.forms import PrettyJSONWidget


class ModelAdmin(DjangoModelAdmin):
    formfield_overrides = {JSONField: {"widget": PrettyJSONWidget}}


class StackedInline(DjangoStackedInline):
    formfield_overrides = {JSONField: {"widget": PrettyJSONWidget}}


class TabularInline(DjangoTabularInline):
    formfield_overrides = {JSONField: {"widget": PrettyJSONWidget}}
