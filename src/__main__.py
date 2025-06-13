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
from emails.commands import cli as emails_cli

cli = typer.Typer(
    name="Tenzu Manager",
    help="Manage a Tenzu server.",
    add_completion=True,
    pretty_exceptions_enable=False,
)


@cli.callback()
def main() -> None:
    pass


# Load module commands
cli.add_typer(emails_cli, name="emails")
cli.add_typer(i18n_cli, name="i18n")


if __name__ == "__main__":
    cli()
