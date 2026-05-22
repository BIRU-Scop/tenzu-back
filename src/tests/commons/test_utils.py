# Copyright (C) 2024-2026 BIRU
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
from unittest.mock import patch

import pytest
from pydantic import AnyHttpUrl

from commons.utils import async_cache, get_absolute_url
from configurations.utils import add_ending_slash, remove_ending_slash


class TestUrlUtils:
    def test_add_ending_slash(self):
        assert add_ending_slash("test") == "test/"
        assert add_ending_slash("test/") == "test/"
        assert add_ending_slash("/te/st") == "/te/st/"
        assert add_ending_slash("/te/st/") == "/te/st/"
        assert add_ending_slash("") == "/"
        assert add_ending_slash("//") == "//"

    def test_remove_ending_slash(self):
        assert remove_ending_slash("test") == "test"
        assert remove_ending_slash("test/") == "test"
        assert remove_ending_slash("/te/st") == "/te/st"
        assert remove_ending_slash("/te/st/") == "/te/st"
        assert remove_ending_slash("") == ""
        assert remove_ending_slash("//") == ""

    def test_get_absolute_url(self, settings):
        settings.BACKEND_URL = AnyHttpUrl.build(scheme="http", host="localhost")
        assert get_absolute_url("test") == "test"
        assert get_absolute_url("/te/st") == "http://localhost/te/st"
        assert get_absolute_url("/te/st/") == "http://localhost/te/st/"
        assert get_absolute_url("") == ""
        assert get_absolute_url("//") == "http://localhost/"
        assert str(get_absolute_url(settings.BACKEND_URL)) == "http://localhost/"


class TestCacheUtils:
    @staticmethod
    def inner_function():
        return "OK"

    @async_cache
    async def cached_function(self):
        return self.inner_function()

    async def test_async_cache(self):
        with patch.object(
            TestCacheUtils, "inner_function", autospec=True
        ) as fake_inner_function:
            fake_inner_function.side_effect = (
                NotImplementedError,
                "OK",
                ValueError,
            )
            with pytest.raises(NotImplementedError):
                await self.cached_function()
            assert await self.cached_function() == "OK"
            # next call is cached so exception won't be raised
            assert await self.cached_function() == "OK"
            self.cached_function.cache_clear()
            with pytest.raises(ValueError):
                await self.cached_function()

            assert fake_inner_function.call_count == 3
