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

from datetime import datetime, timedelta, timezone

import pytest
from django.test import override_settings
from jinja2 import Environment, select_autoescape

from base.i18n import i18n
from base.templating.filters import load_filters

env = Environment(autoescape=select_autoescape())
load_filters(env)


#########################################################################################
# wbr_split
#########################################################################################


@pytest.mark.parametrize(
    "text, result",
    [
        ("thisisalongtext", "thisisalongtext"),
        (
            "thisisalongtext1thisisalongtext2thisisalongtext3thisisalongtext4thisisalongtext",
            "thisisalongtext1thisisalongtext2thisisalongtext3thisisalongtext4thisis<wbr>alongtext",
        ),
    ],
)
def test_wbr_split_with_default_size(text, result):
    template = f"{{{{ '{text}' | wbr_split }}}}"
    assert env.from_string(template).render() == result


@pytest.mark.parametrize(
    "text, size, result",
    [
        ("thisisalongtext", 5, "thisi<wbr>salon<wbr>gtext"),
        ("thisisalongtext", 2, "th<wbr>is<wbr>is<wbr>al<wbr>on<wbr>gt<wbr>ex<wbr>t"),
    ],
)
def test_wbr_split_with_custom_size(text, size, result):
    template = f"{{{{ '{text}' | wbr_split({size}) }}}}"
    assert env.from_string(template).render() == result

    template = f"{{{{ '{text}' | wbr_split(size={size}) }}}}"
    assert env.from_string(template).render() == result


#########################################################################################
# format_datetime
#########################################################################################


@pytest.mark.parametrize(
    "value, result",
    [
        ("2022-06-22T14:53:07.351464+02:00", "June 22, 2022, 2:53:07 PM +0200"),
        (
            datetime(
                2022, 6, 22, 14, 53, 7, 351464, tzinfo=timezone(timedelta(hours=2))
            ),
            "June 22, 2022, 2:53:07 PM +0200",
        ),
    ],
)
def test_format_datetime_with_default_format(value, result):
    context = {"value": value}
    template = "{{ value | format_datetime }}"

    with i18n.use("en-US"):
        assert env.from_string(template).render(**context) == result


@pytest.mark.parametrize(
    "value, format, result",
    [
        (
            "2022-06-22T14:53:07.351464+02:00",
            "yyyy.MM.dd G 'at' HH:mm:ss zzz",
            "2022.06.22 AD at 14:53:07 +0200",
        ),
        (
            "2022-06-22T14:53:07.351464+02:00",
            "long",
            "June 22, 2022, 2:53:07 PM +0200",
        ),
        (
            datetime(
                2022, 6, 22, 14, 53, 7, 351464, tzinfo=timezone(timedelta(hours=2))
            ),
            "yyyy.MM.dd G HH:mm:ss zzz",
            "2022.06.22 AD 14:53:07 +0200",
        ),
        (
            datetime(
                2022, 6, 22, 14, 53, 7, 351464, tzinfo=timezone(timedelta(hours=2))
            ),
            "short",
            "6/22/22, 2:53 PM",
        ),
    ],
)
def test_format_datetime_with_custom_format(value, format, result):
    context = {"value": value, "format": format}

    with i18n.use("en-US"):
        template = "{{ value | format_datetime(format) }}"
        assert env.from_string(template).render(**context) == result

        template = "{{ value | format_datetime(format=format) }}"
        assert env.from_string(template).render(**context) == result


#########################################################################################
# static_url
#########################################################################################


def test_static_url():
    with override_settings(**{"STATIC_URL": "http://localhost:8000/static/"}):
        context = {"file": "example/test1.png"}
        template = "{{ file | static_url }}"

        assert (
            env.from_string(template).render(**context)
            == "http://localhost:8000/static/example/test1.png"
        )

    with override_settings(**{"STATIC_URL": "https://tenzu.company.com/static/"}):
        context = {"file": "example/test2.png"}
        template = "{{ file | static_url }}"

        assert (
            env.from_string(template).render(**context)
            == "https://tenzu.company.com/static/example/test2.png"
        )
