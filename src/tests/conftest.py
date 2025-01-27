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


import pytest

# import pytest_asyncio
from django.core.management import call_command

from .fixtures import *  # noqa


#
# Load initial tenzu fixtures
#
@pytest.fixture(scope="function")
def django_db_setup(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        call_command("loaddata", "initial_project_templates.json", verbosity=0)


#
# Start the event manager
#


# @pytest_asyncio.fixture(scope="session", autouse=True)
# async def connect_events_manage_on_startup():
#     from events import connect_events_manager, disconnect_events_manager
#
#     await connect_events_manager()
#     yield
#     await disconnect_events_manager()


#
# Manage slow tests
#
def pytest_addoption(parser):
    parser.addoption(
        "--slow_only", action="store_true", default=False, help="run slow tests only"
    )

    parser.addoption(
        "--fast_only", action="store_true", default=False, help="exclude slow tests"
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--slow_only"):
        skip = pytest.mark.skip(reason="only execute slow test")
        for item in items:
            # Only those with django_db(transaction=true)
            if "django_db" not in item.keywords:
                item.add_marker(skip)
            else:
                for marker in item.iter_markers(name="django_db"):
                    if not marker.kwargs.get("transaction", False):
                        item.add_marker(skip)
                        break
    elif config.getoption("--fast_only"):
        skip = pytest.mark.skip(reason="exclude slow test")
        for item in items:
            # Exclude those with django_db(transaction=true)
            for marker in item.iter_markers(name="django_db"):
                if marker.kwargs.get("transaction", False):
                    item.add_marker(skip)
                    break
