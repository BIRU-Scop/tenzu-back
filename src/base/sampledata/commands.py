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

import typer

from base.utils.concurrency import run_async_as_sync

cli = typer.Typer(
    name="The Tenzu sample data Manager",
    help="Manage Tenzu sample data.",
    add_completion=True,
)


@cli.callback(invoke_without_command=True, help="Load sampledata")
def load(
    test: bool = typer.Option(
        True,
        " / --no-test",
        " / -nt",
        help="Not load test data (only demo data)",
    ),
    demo: bool = typer.Option(
        True,
        " / --no-demo",
        " / -nd",
        help="Not load demo data (only test data)",
    ),
) -> None:
    from base.sampledata.demo_data import load_demo_data
    from base.sampledata.test_data import load_test_data

    if test:
        run_async_as_sync(load_test_data())

    if demo:
        run_async_as_sync(load_demo_data())
