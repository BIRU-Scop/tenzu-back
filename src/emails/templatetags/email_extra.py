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
from django.templatetags.static import StaticNode
from django.utils.html import conditional_escape
from django.utils.http import urlencode
from django.utils.safestring import mark_safe
from django.utils.translation import ngettext

from commons.front import Urls
from commons.front.exceptions import InvalidFrontUrl
from commons.utils import get_absolute_url

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


class AbsoluteStaticNode(StaticNode):
    def render(self, context):
        url = super().render(context)
        if self.varname is None:
            return get_absolute_url(url)
        context[self.varname] = get_absolute_url(url)
        return url


@register.tag()
def absolute_static(parser, token):
    """
    This tag generate a complete URL -- e.g, http://localhost:8000/static/emails/tenzu.png --
    based on the static files configuration in the settings module and the relative file path.

    .. sourcecode:: django-template
        <img src="{% absolute_static 'emails/logo.png' %}" alt="" />

    .. sourcecode:: html
        <img src="http://localhost:8000/static/emails/logo.png" alt="" />
    """
    return AbsoluteStaticNode.handle_token(parser, token)


@register.filter(needs_autoescape=True)
def wbr_split(text: str, size: int = 70, autoescape=True):
    """
    This filter is used to split large strings at ``text`` by introducing the html tag <wbr> every 70 characters, by
    default, according to ``size`` attribute.

    .. sourcecode:: django-template
        {{ "thisisaverylongword1thisisaverylongword2thisisaverylongword3thisisaverylongword4" | wbr_split }}

    .. sourcecode:: html
        thisisaverylongword1thisisaverylongword2thisisaverylongword3thisisaver<wbr>ylongword4

    or with a custom size

    .. sourcecode:: django-template
        {{ "thisisaverylongword" | wbr_split(size=3) }}
        {{ "otherverylongword" | wbr_split(3) }}

    .. sourcecode:: html
        thi<wbr>sis<wbr>ave<wbr>ryl<wbr>ong<wbr>str<wbr>ing
        oth<wbr>erv<wbr>ery<wbr>lon<wbr>gwo<wbr>rd

    """
    esc = conditional_escape if autoescape else lambda x: x
    result = "<wbr/>".join([esc(text[x : x + size]) for x in range(0, len(text), size)])
    return mark_safe(result)


@register.filter
def display_lifetime(lifetime: timedelta) -> str:
    """
    This function takes timedelta and return a string to round it to days, hours or minutes.
    If minutes are less than a day, then it returns hours.
    If minutes are less than an hour, then it returns the minutes.
    """
    if lifetime.days > 0:
        return ngettext(
            "datetime.lifetime.day %(count)d",
            "datetime.lifetime.days %(count)d",
            lifetime.days,
        ) % {"count": lifetime.days}
    else:
        hours, remainder = divmod(lifetime.seconds, 3600)
        if hours > 0:
            return ngettext(
                "datetime.lifetime.hour %(count)d",
                "datetime.lifetime.hours %(count)d",
                hours,
            ) % {"count": hours}
        else:
            minutes = remainder // 60
            return ngettext(
                "datetime.lifetime.minute %(count)d",
                "datetime.lifetime.minutes %(count)d",
                minutes,
            ) % {"count": minutes}
