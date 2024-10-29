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

from pathlib import Path
from typing import Final

import typer

from base.i18n import i18n
from base.utils import json, pprint
from configurations.conf import settings
from emails import render as email_render
from emails.emails import EmailPart, Emails

TEMPLATES_PATH: Final[Path] = Path(__file__).resolve().parent.joinpath("templates")  # src/tenzu/emails/templates


cli = typer.Typer(
    name="The Tenzu Email Manager",
    help="Manage Tenzu emails.",
    add_completion=True,
)


@cli.command(help="Show available emails")
def list() -> None:
    for email in Emails:
        typer.echo(f"\t{ email.value }")


@cli.command(help="Render one email part to test it")
def render(
    part: EmailPart = typer.Option(EmailPart.HTML.value, "--part", "-p", help="Part of the email to render."),
    lang: str = typer.Option(
        settings.LANG,
        "--lang",
        "-l",
        help=f"Language used to render. Availables are: {', '.join(i18n.available_languages)}.",
    ),
    email: Emails = typer.Argument(..., case_sensitive=False, help="Name of the email"),
) -> None:
    email_name = email.value

    # Get context
    context_json = TEMPLATES_PATH.joinpath(f"{email_name}.json")
    try:
        with open(context_json) as context_file:
            context = json.loads(context_file.read())
    except FileNotFoundError:
        context = {}

    # Print email parti
    console = pprint.Console()
    with i18n.use(lang):
        match part:
            case EmailPart.SUBJECT:
                syntax = pprint.Syntax(email_render.render_subject(email_name, context), "txt")
                console.print(syntax)
            case EmailPart.TXT:
                syntax = pprint.Syntax(email_render.render_email_txt(email_name, context), "txt")
                console.print(syntax)
            case EmailPart.HTML:
                syntax = pprint.Syntax(email_render.render_email_html(email_name, context), "html")
                console.print(syntax)
