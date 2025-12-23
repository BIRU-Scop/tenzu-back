# Copyright (C) 2025 BIRU
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

from functools import wraps

from allauth.headless.constants import Client
from allauth.headless.internal.decorators import mark_request_as_headless
from asgiref.sync import iscoroutinefunction


def add_allauth_properties(view_func):
    if iscoroutinefunction(view_func):

        async def _view_wrapper(request, *args, **kwargs):
            mark_request_as_headless(request, Client.BROWSER)
            return await view_func(request, *args, **kwargs)

    else:

        def _view_wrapper(request, *args, **kwargs):
            mark_request_as_headless(request, Client.BROWSER)
            return view_func(request, *args, **kwargs)

    return wraps(view_func)(_view_wrapper)
