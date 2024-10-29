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

# Copyright 2021 Ezeudoh Tochukwu
# https://github.com/eadwinCode/django-ninja-jwt
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import BlacklistedToken, OutstandingToken


class OutstandingTokenAdmin(admin.ModelAdmin):
    list_display = (
        "jti",
        "user",
        "created_at",
        "expires_at",
    )
    search_fields = (
        "user__id",
        "jti",
    )
    ordering = ("user",)

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)

        return qs.select_related("user")

    # Read-only behavior defined below
    actions = None

    def get_readonly_fields(self, *args, **kwargs):
        return [f.name for f in self.model._meta.fields]

    def has_add_permission(self, *args, **kwargs):
        return False

    def has_delete_permission(self, *args, **kwargs):
        return False

    def has_change_permission(self, request, obj=None):
        return request.method in [
            "GET",
            "HEAD",
        ] and super().has_change_permission(  # noqa: W504
            request, obj
        )


admin.site.register(OutstandingToken, OutstandingTokenAdmin)


class BlacklistedTokenAdmin(admin.ModelAdmin):
    list_display = (
        "token_jti",
        "token_user",
        "token_created_at",
        "token_expires_at",
        "blacklisted_at",
    )
    search_fields = (
        "token__user__id",
        "token__jti",
    )
    ordering = ("token__user",)

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)

        return qs.select_related("token__user")

    def token_jti(self, obj):
        return obj.token.jti

    token_jti.short_description = _("jti")
    token_jti.admin_order_field = "token__jti"

    def token_user(self, obj):
        return obj.token.user

    token_user.short_description = _("user")
    token_user.admin_order_field = "token__user"

    def token_created_at(self, obj):
        return obj.token.created_at

    token_created_at.short_description = _("created at")
    token_created_at.admin_order_field = "token__created_at"

    def token_expires_at(self, obj):
        return obj.token.expires_at

    token_expires_at.short_description = _("expires at")
    token_expires_at.admin_order_field = "token__expires_at"


admin.site.register(BlacklistedToken, BlacklistedTokenAdmin)
