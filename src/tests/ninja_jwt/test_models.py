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


import pytest

from ninja_jwt.models import TokenUser
from ninja_jwt.settings import api_settings

AuthToken = api_settings.AUTH_TOKEN_CLASSES[0]


class TestTokenUser:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.token = AuthToken()
        self.token[api_settings.USER_ID_CLAIM] = 42
        self.token["username"] = "deep-thought"
        self.token["some_other_stuff"] = "arstarst"

        self.user = TokenUser(self.token)

    def test_username(self):
        assert self.user.username == "deep-thought"

    def test_is_active(self):
        assert self.user.is_active

    def test_str(self):
        assert str(self.user) == "TokenUser 42"

    def test_id(self):
        assert self.user.id == 42

    def test_pk(self):
        assert self.user.pk == 42

    def test_is_staff(self):
        payload = {api_settings.USER_ID_CLAIM: 42}
        user = TokenUser(payload)

        assert not user.is_staff

        payload["is_staff"] = True
        user = TokenUser(payload)

        assert user.is_staff

    def test_is_superuser(self):
        payload = {api_settings.USER_ID_CLAIM: 42}
        user = TokenUser(payload)

        assert not user.is_superuser

        payload["is_superuser"] = True
        user = TokenUser(payload)

        assert user.is_superuser

    def test_eq(self):
        user1 = TokenUser({api_settings.USER_ID_CLAIM: 1})
        user2 = TokenUser({api_settings.USER_ID_CLAIM: 2})
        user3 = TokenUser({api_settings.USER_ID_CLAIM: 1})

        assert user1 != user2
        assert user1 == user3

    def test_hash(self):
        assert hash(self.user) == hash(self.user.id)

    def test_not_implemented(self):
        with pytest.raises(NotImplementedError):
            self.user.save()

        with pytest.raises(NotImplementedError):
            self.user.delete()

        with pytest.raises(NotImplementedError):
            self.user.set_password("arst")

        with pytest.raises(NotImplementedError):
            self.user.check_password("arst")

    def test_groups(self):
        assert not self.user.groups.exists()

    def test_user_permissions(self):
        assert not self.user.user_permissions.exists()

    def test_get_group_permissions(self):
        assert len(self.user.get_group_permissions()) == 0

    def test_get_all_permissions(self):
        assert len(self.user.get_all_permissions()) == 0

    def test_has_perm(self):
        assert not self.user.has_perm("test_perm")

    def test_has_perms(self):
        assert not self.user.has_perms(["test_perm"])

    def test_has_module_perms(self):
        assert not self.user.has_module_perms("test_module")

    def test_is_anonymous(self):
        assert not self.user.is_anonymous

    def test_is_authenticated(self):
        assert self.user.is_authenticated

    def test_get_username(self):
        assert self.user.get_username() == "deep-thought"
