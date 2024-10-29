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

#
# The code is partially taken (and modified) from djangorestframework-simplejwt v. 4.7.1
# (https://github.com/jazzband/djangorestframework-simplejwt/tree/5997c1aee8ad5182833d6b6759e44ff0a704edb4)
# that is licensed under the following terms:
#
#   Copyright 2017 David Sanders
#
#   Permission is hereby granted, free of charge, to any person obtaining a copy of
#   this software and associated documentation files (the "Software"), to deal in
#   the Software without restriction, including without limitation the rights to
#   use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
#   of the Software, and to permit persons to whom the Software is furnished to do
#   so, subject to the following conditions:
#
#   The above copyright notice and this permission notice shall be included in all
#   copies or substantial portions of the Software.
#
#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#   AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#   LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#   OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#   SOFTWARE.

from auth.tokens import AccessToken, RefreshToken
from configurations.conf import settings

##########################################################
# RefreshToken
##########################################################


def test_refresh_token_init():
    # Should set token type claim
    token = RefreshToken()
    assert token[settings.TOKENS.TOKEN_TYPE_CLAIM] == "refresh"


def test_refresh_token_access_token_():
    # Should create an access token from a refresh token
    refresh = RefreshToken()
    refresh["test_claim"] = "arst"

    access = refresh.access_token

    assert isinstance(access, AccessToken)
    assert access[settings.TOKENS.TOKEN_TYPE_CLAIM] == "access"

    # Should keep all copyable claims from refresh token
    assert refresh["test_claim"] == access["test_claim"]

    # Should not copy certain claims from refresh token
    for claim in RefreshToken.no_copy_claims:
        assert access[claim] != refresh[claim]


##########################################################
# AccessToken
##########################################################


def test_access_token_init():
    # Should set token type claim
    token = AccessToken()
    assert token[settings.TOKENS.TOKEN_TYPE_CLAIM] == "access"
