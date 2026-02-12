# Copyright (C) 2026 BIRU
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

from datetime import timedelta
from typing import Any
from urllib.parse import urljoin

from django import template
from django.conf import settings
from django.utils.http import urlencode
from django.utils.translation import ngettext
from markupsafe import Markup

from commons.front import Urls
from commons.front.exceptions import InvalidFrontUrl

register = template.Library()


@register.simple_tag
def front_url(
    url_key: str, query_params: dict[str, str] | None = None, **kwargs: Any
) -> str:
    try:
        url_pattern = Urls[url_key]
    except KeyError:
        raise InvalidFrontUrl(f"Theres no front-end url matching the key `{url_key}`")

    url = urljoin(str(settings.FRONTEND_URL), str(url_pattern.value.format(**kwargs)))

    if query_params:
        return f"{url}?{urlencode(query_params)}"

    return url


@register.filter
def wbr_split(text: str, size: int = 70) -> Markup:
    """
    This filter is used to split large strings at ``text`` by introducing the html tag <wbr> every 70 characters, by
    default, according to ``size`` attribute.

    .. sourcecode:: jinja
        {% set long_word = "thisisaverylongword1thisisaverylongword2thisisaverylongword3thisisaver<wbr>ylongword4" %}
        {{ long_word | wbr_split }}

    .. sourcecode:: html
        thisisaverylongword1thisisaverylongword2thisisaverylongword3thisisaver<wbr>ylongword4

    or with a custom size

    .. sourcecode:: jinja
        {{ "thisisaverylongword" | wbr_split(size=3) }}
        {{ "otherverylongword" | wbr_split(3) }}

    .. sourcecode:: html
        thi<wbr>sis<wbr>ave<wbr>ryl<wbr>ong<wbr>str<wbr>ing
        oth<wbr>erv<wbr>ery<wbr>lon<wbr>gwo<wbr>rd

    """
    return Markup("<wbr>").join([text[x : x + size] for x in range(0, len(text), size)])


@register.filter
def display_lifetime(lifetime: timedelta) -> str:
    """
    This function takes timedelta and return a string to round it to days, hours or minutes.
    If minutes are less than a day, then it returns hours.
    If minutes are less than an hour, then it returns the minutes.
    """
    if lifetime.days > 0:
        return (
            ngettext("datetime.lifetime.day", "datetime.lifetime.days", lifetime.days)
            % lifetime.days
        )
    else:
        hours, remainder = divmod(lifetime.seconds, 3600)
        if hours > 0:
            return (
                ngettext("datetime.lifetime.hour", "datetime.lifetime.hours", hours)
                % hours
            )
        else:
            minutes = remainder // 60
            return (
                ngettext(
                    "datetime.lifetime.minute", "datetime.lifetime.minutes", minutes
                )
                % minutes
            )
