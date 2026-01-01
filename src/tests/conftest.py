# -*- coding: utf-8 -*-
# Copyright (C) 2024-2025 BIRU
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
import contextlib
import os
from unittest import mock
from unittest.mock import patch

import pytest
from django.db import connections

# import pytest_asyncio
from .fixtures import *  # noqa

# /!\ If you are using TransactionalTestCase (using "pytest.mark.django_db(transaction=True)" or "transactional_db" fixture)
# initial data loaded in migrations will NOT be available (see https://docs.djangoproject.com/en/5.2/topics/testing/overview/#rollback-emulation)
# If you need data migration in your test (like the ProjectTemplate instance required by "project_template" fixture)
# Either use simple TestCase if you can, or add the "serialized_rollback=True" argument to pytest.mark.django_db
# or the "django_db_serialized_rollback" fixture to make migrated data available in your tests


@pytest.fixture(autouse=True)
def fix_async_db(request):
    """
    If you don't use this fixture for async tests that use the ORM/database
    you won't get proper teardown of the database.
    This is a bug somewhere in pytest-django, pytest-asyncio or django itself.

    Nobody knows how to solve it, or who should solve it.
    Workaround here: https://github.com/pytest-dev/pytest-asyncio/issues/226#issuecomment-2225156564
    More info:
    https://github.com/pytest-dev/pytest-django/issues/580
    https://github.com/pytest-dev/pytest-asyncio/issues/226


    The actual implementation of this workaround consists on ensuring
    Django always returns the same database connection independently of the thread
    the code that requests a db connection is in.

    We were unable to use better patching methods (the target is asgiref/local.py),
    so we resorted to mocking the _lock_storage context manager so that it returns a Mock.
    That mock contains the default connection of the main thread (instead of the connection
    of the running thread).

    This only works because our tests only ever use the default connection, which is the only thing our mock returns.
    """
    marker = request.node.get_closest_marker("django_db")
    if (
        marker is None or marker.kwargs.get("transaction", False)
    ) or request.node.get_closest_marker("asyncio") is None:
        # Only run for async tests that use the database and no transaction
        yield
        return

    main_thread_local = connections._connections
    for conn in connections.all():
        conn.inc_thread_sharing()

    main_thread_default_conn = main_thread_local._storage.default
    main_thread_storage = main_thread_local._lock_storage

    @contextlib.contextmanager
    def _lock_storage():
        yield mock.Mock(default=main_thread_default_conn)

    try:
        with patch.object(main_thread_default_conn, "close"):
            object.__setattr__(main_thread_local, "_lock_storage", _lock_storage)
            yield
    finally:
        object.__setattr__(main_thread_local, "_lock_storage", main_thread_storage)


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


def _is_parallel_run():
    # detect if we are using pytest-xdist parallel mode
    return os.environ.get("PYTEST_XDIST_WORKER", None) is not None


def pytest_collection_modifyitems(config, items):
    def handle_filtering_options():
        if config.getoption("--slow_only"):
            skip = pytest.mark.skip(reason="only execute slow test")
            for item in items:
                # Only those with django_db(transaction=True or serialized_rollback=True)
                if "django_db" not in item.keywords:
                    item.add_marker(skip)
                else:
                    for marker in item.iter_markers(name="django_db"):
                        if not marker.kwargs.get(
                            "transaction", False
                        ) and not marker.kwargs.get("serialized_rollback", False):
                            item.add_marker(skip)
                            break
        elif config.getoption("--fast_only"):
            skip = pytest.mark.skip(reason="exclude slow test")
            for item in items:
                # Exclude those with django_db(transaction=True or serialized_rollback=True)
                for marker in item.iter_markers(name="django_db"):
                    if marker.kwargs.get("transaction", False) or marker.kwargs.get(
                        "serialized_rollback", False
                    ):
                        item.add_marker(skip)
                        break

    handle_filtering_options()

    parallel_run = _is_parallel_run()

    # make every tests using db with transaction=True but not serialized_rollback=True
    # run at the end, otherwise you'll get flaky tests with IntegrityError: duplicate key because
    # serialised data are loaded once by post_migrate on teardown of a test with serialized_rollback=False
    # and a second time by serialised data when serialized_rollback=True
    # see https://code.djangoproject.com/ticket/36429
    def transactional_attr_order(item):
        marker = item.get_closest_marker("django_db")
        if marker:
            if parallel_run:
                # mark all test using the db as flaky, as running them in parallel with pytest-xdist can cause db concurrency issue
                item.add_marker(pytest.mark.flaky(only_rerun=["AssertionError"]))
            if marker.kwargs.get("transaction", False) and not marker.kwargs.get(
                "serialized_rollback", False
            ):
                return 1
        return 0

    items.sort(key=transactional_attr_order)
