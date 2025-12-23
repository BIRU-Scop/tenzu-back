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

import pytest
from procrastinate import App, testing
from procrastinate.contrib.django import procrastinate_app
from procrastinate.testing import JobRow


class TestTasksQueueManager:
    _app: App

    def __init__(self, app: App) -> None:
        self._app = app
        self.reset()

    def run(self) -> None:
        return self._app.run_worker(wait=False)

    async def run_async(self) -> None:
        return await self._app.run_worker_async(wait=False)

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
def in_memory_app():
    in_memory = testing.InMemoryConnector()

    with procrastinate_app.current_app.replace_connector(in_memory) as app:
        yield app


@pytest.fixture
def tqmanager(in_memory_app) -> TestTasksQueueManager:
    return TestTasksQueueManager(in_memory_app)
