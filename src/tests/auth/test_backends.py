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

from django.contrib.auth import authenticate

from tests.utils.factories import create_user


class TestEmailOrUsernameModelBackend:
    def test_it_should_return_the_correct_values(self, db):
        password = "secret-pwd"
        user = create_user(email="test@email.com", username="test", password=password)
        assert user == authenticate(None, username=user.username, password=password)
        assert user == authenticate(None, username=user.email, password=password)
        assert authenticate(None, random_field="", password=password) is None
