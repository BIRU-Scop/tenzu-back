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

from pathlib import Path
from typing import Final

import orjson
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import translation
from rich.console import Console
from rich.syntax import Syntax

from commons import i18n
from emails import render as email_render
from emails.emails import EmailPart, Emails

TEMPLATES_PATH: Final[Path] = (
    Path(__file__).resolve().parent.joinpath("templates")
)  # src/tenzu/emails/templates


class Command(BaseCommand):
    help = "Render one email part to test it"

    def add_arguments(self, parser):
        parser.add_argument(
            "--part",
            "-p",
            help="Part of the email to render.",
            default=EmailPart.HTML.value,
            type=EmailPart,
        )
        parser.add_argument(
            "--lang",
            "-l",
            help=f"Language used to render. Availables are: {', '.join(i18n.get_available_languages())}.",
            default=settings.LANGUAGE_CODE,
        )
        parser.add_argument("email", help="Part of the email to render.", type=Emails)

    def handle(self, *args, **options):
        email_name = options["email"].value

        # Get context
        context_json = TEMPLATES_PATH.joinpath(f"{email_name}.json")
        try:
            with open(context_json) as context_file:
                context = orjson.loads(context_file.read())
        except FileNotFoundError:
            context = {}

        # Print email part
        console = Console()
        with translation.override(options["lang"]):
            match options["part"]:
                case EmailPart.SUBJECT:
                    syntax = Syntax(
                        email_render.render_subject(email_name, context), "txt"
                    )
                    console.print(syntax)
                case EmailPart.TXT:
                    syntax = Syntax(
                        email_render.render_email_txt(email_name, context), "txt"
                    )
                    console.print(syntax)
                case EmailPart.HTML:
                    syntax = Syntax(
                        email_render.render_email_html(email_name, context), "html"
                    )
                    console.print(syntax)
