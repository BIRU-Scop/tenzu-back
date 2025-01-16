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
from procrastinate import App, testing
from procrastinate.contrib.django import procrastinate_app
from procrastinate.testing import JobRow


class TestTasksQueueManager:
    _app: App

    def __init__(self, app: App) -> None:
        self._app = app
        self.reset()

    @property
    def jobs(self) -> dict[int, JobRow]:
        return self._app.connector.jobs  # type: ignore[attr-defined]

    @property
    def pending_jobs(self) -> list[JobRow]:
        return [
            job
            for job in self.jobs.values()
            if job["status"] not in ["failed", "succeeded"]
        ]

    @property
    def finished_jobs(self) -> list[JobRow]:
        return self._app.connector.finished_jobs  # type: ignore[attr-defined]

    @property
    def failed_jobs(self) -> list[JobRow]:
        return [job for job in self.jobs.values() if job["status"] == "failed"]

    @property
    def succeeded_jobs(self) -> list[JobRow]:
        return [job for job in self.jobs.values() if job["status"] == "succeeded"]

    def reset(self) -> None:
        self._app.connector.reset()  # type: ignore[attr-defined]


@pytest.fixture(autouse=True)
def in_memory_app(monkeypatch) -> App:
    app = procrastinate_app.current_app.with_connector(testing.InMemoryConnector())
    monkeypatch.setattr(procrastinate_app, "current_app", app)
    return app


@pytest.fixture
def tqmanager(in_memory_app) -> TestTasksQueueManager:
    return TestTasksQueueManager(in_memory_app)


# TODO update tests using tqmanager to actually check for jobs count once we have upgraded our task manager
