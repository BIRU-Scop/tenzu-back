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


from django.conf import settings

from tokens.base import DenylistMixin, Token


class VerifyUserToken(DenylistMixin, Token):
    token_type = "verify-user"
    lifetime = settings.VERIFY_USER_TOKEN_LIFETIME
    is_unique = True


class ResetPasswordToken(DenylistMixin, Token):
    token_type = "reset-password"
    lifetime = settings.RESET_PASSWORD_TOKEN_LIFETIME
