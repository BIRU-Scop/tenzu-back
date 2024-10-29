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

import pytest

from base.utils import emails


@pytest.mark.parametrize(
    "first_email, second_email, expected",
    [
        # True
        ("test@email.com", "test@email.com", True),
        ("TEST@EMAIL.COM", "test@email.com", True),
        ("test@email.com", "TEST@EMAIL.COM", True),
        ("test@email.com", "teST@EMail.com", True),
        ("test@emaIL.COm", "test@email.com", True),
        ("te+st@email.com", "te+st@email.com", True),
        ("test@subdomain.email.com", "test@subdomain.email.com", True),
        # False
        ("test1@email.com", "test@email.com", False),
        ("test@email.com", "other@email.com", False),
        ("test@email.com", "test@bemail.es", False),
        ("test@email.com", "tes.t@email.com", False),
        ("tes+t@email.com", "test@email.com", False),
    ],
)
async def test_emails_are_the_same(first_email, second_email, expected):
    assert emails.are_the_same(first_email, second_email) == expected


@pytest.mark.parametrize(
    "value, expected",
    [
        # True
        ("test@email.com", True),
        ("test+something@email.com", True),
        ("test.123@email.com", True),
        ("test@emaIL.comm", True),
        ("test@subdomain.email.com", True),
        # False
        ("test1@com", False),
        ("test@", False),
        ("test", False),
        ("test@.com", False),
        ("test@email.", False),
        ("@email.", False),
    ],
)
async def test_is_email(value, expected):
    assert emails.is_email(value) == expected
