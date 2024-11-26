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

import logging

import typer
from babel.messages import frontend as babel_cli
from django.conf import settings

from base.i18n import (
    FALLBACK_LOCALE_CODE,
    ROOT_DIR,
    TRANSLATION_DIRECTORY,
    get_locale_code,
    i18n,
)
from base.utils import pprint
from base.utils.commands import set_working_directory

logger = logging.getLogger(__name__)


cli = typer.Typer(
    name="The Tenzu i18n Manager",
    help="Manage Tenzu translations.",
    add_completion=True,
)


@cli.command(help="List available languages")
def list_languages() -> None:
    table = pprint.Table(title="Available languages")
    table.add_column("Code", style="bold yellow")
    table.add_column("Name (EN)")
    table.add_column("Language")
    table.add_column("Territory")
    table.add_column("Extra", style="italic")

    for loc in i18n.locales:
        code = get_locale_code(loc)
        name = loc.english_name
        language = loc.language_name
        territory = loc.territory_name
        extra: list[str] = []
        if code == FALLBACK_LOCALE_CODE:
            extra.append("fallback")
        if code == settings.LANGUAGE_CODE:
            extra.append("default")

        table.add_row(code, name, language, territory, ", ".join(extra))

    console = pprint.Console()
    console.print(table)


def _extract_messages() -> None:
    src_path = ROOT_DIR.parent  # src/

    with set_working_directory(src_path):
        extract_cmd = babel_cli.extract_messages()
        extract_cmd.mapping_file = str(src_path.joinpath("../babel.cfg"))
        extract_cmd.output_file = str(TRANSLATION_DIRECTORY.joinpath("messages.pot"))
        extract_cmd.input_paths = "./"
        extract_cmd.finalize_options()
        extract_cmd.run()


@cli.command(help="Add a new language to the catalog if it does not exist")
def add_language(locale_code: str) -> None:
    catalog_file = TRANSLATION_DIRECTORY.joinpath("messages.pot")

    if not catalog_file.exists():
        _extract_messages()

    if locale_code not in i18n.global_languages:
        pprint.print(f"[red]Language code '{locale_code}' does not exist[/red]")
        pprint.print(
            f"Valid Language code are: [green]{'[/green], [green]'.join(i18n.global_languages)}[/green]"
        )
        raise typer.Exit(code=1)

    if i18n.is_language_available(locale_code):
        pprint.print(f"[yellow]Language '{locale_code}' already exist[/yellow]")
        raise typer.Exit()

    cmd = babel_cli.init_catalog()
    cmd.input_file = str(catalog_file)
    cmd.output_dir = str(TRANSLATION_DIRECTORY)
    cmd.locale = locale_code.replace("-", "_")
    cmd.finalize_options()
    cmd.run()
    pprint.print(f"[green]Language '{locale_code}' added[/green]")


@cli.command(help="Update catalog (code to .po)")
def update_catalog() -> None:
    _extract_messages()

    cmd = babel_cli.update_catalog()
    cmd.input_file = str(TRANSLATION_DIRECTORY.joinpath("messages.pot"))
    cmd.output_dir = str(TRANSLATION_DIRECTORY)
    cmd.finalize_options()
    cmd.run()
    pprint.print("[green]Catalog updated[/green]")


@cli.command(help="Compile catalog (.po to .mo)")
def compile_catalog() -> None:
    cmd = babel_cli.compile_catalog()
    cmd.directory = str(TRANSLATION_DIRECTORY)
    cmd.finalize_options()
    cmd.run()  # type: ignore[no-untyped-call]
    pprint.print("[green]Catalog compiled[/green]")
