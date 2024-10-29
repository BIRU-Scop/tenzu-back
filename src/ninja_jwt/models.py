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

from typing import Any

from django.contrib.auth import models as auth_models
from django.db.models.manager import EmptyManager
from django.utils.functional import cached_property

from .settings import api_settings


class TokenUser:
    """
    A dummy user class modeled after django.contrib.auth.models.AnonymousUser.
    Used in conjunction with the `JWTStatelessUserAuthentication` backend to
    implement single sign-on functionality across services which share the same
    secret key.  `JWTStatelessUserAuthentication` will return an instance of this
    class instead of a `User` model instance.  Instances of this class act as
    stateless user objects which are backed by validated tokens.
    """

    # User is always active since Simple JWT will never issue a token for an
    # inactive user
    is_active = True

    _groups = EmptyManager(auth_models.Group)
    _user_permissions = EmptyManager(auth_models.Permission)

    def __init__(self, token: Any) -> None:
        self.token = token

    def __str__(self) -> str:
        return "TokenUser {}".format(self.id)

    @cached_property
    def id(self) -> Any:
        return self.token[api_settings.USER_ID_CLAIM]

    @cached_property
    def pk(self) -> Any:
        return self.id

    @cached_property
    def username(self) -> str:
        return self.token.get("username", "")

    @cached_property
    def is_staff(self) -> bool:
        return self.token.get("is_staff", False)

    @cached_property
    def is_superuser(self) -> bool:
        return self.token.get("is_superuser", False)

    def __eq__(self, other) -> bool:
        return self.id == other.id

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return hash(self.id)

    def save(self) -> None:
        raise NotImplementedError("Token users have no DB representation")

    def delete(self) -> None:
        raise NotImplementedError("Token users have no DB representation")

    def set_password(self, raw_password: str) -> None:
        raise NotImplementedError("Token users have no DB representation")

    def check_password(self, raw_password: str) -> None:
        raise NotImplementedError("Token users have no DB representation")

    @property
    def groups(self) -> EmptyManager:
        return self._groups

    @property
    def user_permissions(self) -> EmptyManager:
        return self._user_permissions

    def get_group_permissions(self, obj=None) -> set:
        return set()

    def get_all_permissions(self, obj=None) -> set:
        return set()

    def has_perm(self, perm, obj=None) -> bool:
        return False

    def has_perms(self, perm_list, obj=None) -> bool:
        return False

    def has_module_perms(self, module) -> bool:
        return False

    @property
    def is_anonymous(self) -> bool:
        return False

    @property
    def is_authenticated(self) -> bool:
        return True

    def get_username(self) -> str:
        return self.username

    def __getattr__(self, attr):
        """This acts as a backup attribute getter for custom claims defined in Token serializers."""
        return self.token.get(attr, None)
