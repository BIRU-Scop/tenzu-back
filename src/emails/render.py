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

from typing import Any, Final

from base.templating import env

TXT_BODY_TEMPLATE_SUFFIX: Final[str] = ".txt.jinja"
HTML_BODY_TEMPLATE_SUFFIX: Final[str] = ".html"
SUBJECT_TEMPLATE_SUFFIX: Final[str] = ".subject.jinja"


def render_email_html(email_name: str, context: dict[str, Any]) -> str:
    html = f"{email_name}{HTML_BODY_TEMPLATE_SUFFIX}"
    template_html = env.get_template(html)
    return template_html.render(context)


def render_subject(email_name: str, context: dict[str, Any]) -> str:
    html = f"{email_name}{SUBJECT_TEMPLATE_SUFFIX}"
    template_html = env.get_template(html)
    return template_html.render(context).replace("\n", "")


def render_email_txt(email_name: str, context: dict[str, Any]) -> str:
    txt = f"{email_name}{TXT_BODY_TEMPLATE_SUFFIX}"
    template_txt = env.get_template(txt)
    return template_txt.render(context)
