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

from base.utils.concurrency import run_async_as_sync
from tokens.services import clean_expired_tokens

logger = logging.getLogger(__name__)


cli = typer.Typer(
    name="The Tenzu Tokens Manager",
    help="Manage Tenzu tokens.",
    add_completion=True,
)


@cli.command(help="Clean expired tokens")
def clean() -> None:
    run_async_as_sync(clean_expired_tokens())
