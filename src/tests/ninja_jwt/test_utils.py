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


from datetime import UTC, datetime, timedelta

from django.test.utils import override_settings
from django.utils import timezone
from freezegun import freeze_time

from ninja_jwt.utils import (
    aware_utcnow,
    datetime_from_epoch,
    datetime_to_epoch,
    format_lazy,
    make_utc,
)


class TestMakeUtc:
    def test_it_should_return_the_correct_values(self):
        # It should make a naive datetime into an aware, utc datetime if django
        # is configured to use timezones and the datetime doesn't already have
        # a timezone

        # Naive datetime
        dt = datetime(year=1970, month=12, day=1)

        with override_settings(USE_TZ=False):
            dt = make_utc(dt)
            assert timezone.is_naive(dt)

        with override_settings(USE_TZ=True):
            dt = make_utc(dt)
            assert timezone.is_aware(dt)
            assert dt.utcoffset() == timedelta(seconds=0)


class TestAwareUtcnow:
    def test_it_should_return_the_correct_value(self):
        now = datetime.now(tz=UTC).replace(tzinfo=None)

        with freeze_time(now):
            # Should return aware utcnow if USE_TZ == True
            with override_settings(USE_TZ=True):
                assert timezone.make_aware(now, timezone=UTC) == aware_utcnow()

            # Should return naive utcnow if USE_TZ == False
            with override_settings(USE_TZ=False):
                assert now == aware_utcnow()


class TestDatetimeToEpoch:
    def assertEqual(self, value_1, value_2):
        assert value_1 == value_2

    def test_it_should_return_the_correct_values(self):
        self.assertEqual(datetime_to_epoch(datetime(year=1970, month=1, day=1)), 0)
        self.assertEqual(
            datetime_to_epoch(datetime(year=1970, month=1, day=1, second=1)), 1
        )
        self.assertEqual(
            datetime_to_epoch(datetime(year=2000, month=1, day=1)), 946684800
        )


class TestDatetimeFromEpoch:
    def assertEqual(self, value_1, value_2):
        assert value_1 == value_2

    def test_it_should_return_the_correct_values(self):
        with override_settings(USE_TZ=False):
            assert datetime_from_epoch(0) == datetime(year=1970, month=1, day=1)
            assert datetime_from_epoch(1) == datetime(
                year=1970, month=1, day=1, second=1
            )
            assert datetime_from_epoch(946684800) == datetime(year=2000, month=1, day=1)

        with override_settings(USE_TZ=True):
            self.assertEqual(
                datetime_from_epoch(0), make_utc(datetime(year=1970, month=1, day=1))
            )
            self.assertEqual(
                datetime_from_epoch(1),
                make_utc(datetime(year=1970, month=1, day=1, second=1)),
            )
            self.assertEqual(
                datetime_from_epoch(946684800),
                make_utc(datetime(year=2000, month=1, day=1)),
            )


class TestFormatLazy:
    def test_it_should_work(self):
        obj = format_lazy("{} {}", "arst", "zxcv")

        assert not isinstance(obj, str)
        assert str(obj) == "arst zxcv"
