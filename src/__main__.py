#!/usr/bin/env python
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

# ruff: noqa: E402

import os

import django

os.environ["DJANGO_SETTINGS_MODULE"] = "configurations.settings"
django.setup()


import typer

from base.i18n.commands import cli as i18n_cli
from base.sampledata.commands import cli as sampledata_cli
from commons.storage.commands import cli as storage_cli
from emails.commands import cli as emails_cli
from notifications.commands import cli as notifications_cli
from tmp import __version__
from tokens.commands import cli as tokens_cli
from users.commands import cli as users_cli

cli = typer.Typer(
    name="Tenzu Manager",
    help="Manage a Tenzu server.",
    add_completion=True,
    pretty_exceptions_enable=False,
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"Tenzu {__version__}")
        raise typer.Exit()


@cli.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Show version information.",
    ),
) -> None:
    pass


# Load module commands
cli.add_typer(emails_cli, name="emails")
cli.add_typer(i18n_cli, name="i18n")
cli.add_typer(notifications_cli, name="notifications")
cli.add_typer(sampledata_cli, name="sampledata")
cli.add_typer(storage_cli, name="storage")
cli.add_typer(tokens_cli, name="tokens")
cli.add_typer(users_cli, name="users")


if __name__ == "__main__":
    cli()
