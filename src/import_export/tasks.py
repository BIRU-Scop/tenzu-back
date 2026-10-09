# -*- coding: utf-8 -*-
# Copyright (C) 2024-2026 BIRU
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

from asgiref.sync import async_to_sync
from django.conf import settings
from django.db import DatabaseError
from procrastinate import JobContext, RetryStrategy
from procrastinate.contrib.django import app

from commons.utils.uuid import decode_b64str_to_uuid
from import_export.models import ProjectImportationPendingInvitation
from import_export.services.taiga import do_import_taiga_project
from stories.stories.services.blocknote import BlockNoteEmptyOutputError

logger = logging.getLogger(__name__)


@app.task(
    retry=RetryStrategy(
        max_attempts=settings.STORAGE.IMPORTATION_RETRY_ATTEMPTS,
        exponential_wait=settings.STORAGE.IMPORTATION_RETRY_EXPONENTIAL_WAIT,
        retry_exceptions={RuntimeError, BlockNoteEmptyOutputError, DatabaseError},
    ),
    pass_context=True,
)
def import_taiga_project(job_context: JobContext, project_importation_id: str) -> None:
    from import_export import services as import_export_services

    importation = async_to_sync(import_export_services.get_project_importation)(
        project_importation_id=decode_b64str_to_uuid(project_importation_id)
    )

    def will_retry(exception: Exception):
        return (
            job_context.task.retry.get_retry_decision(
                exception=exception, job=job_context.job
            )
            is not None
        )

    async_to_sync(do_import_taiga_project)(importation, will_retry)


@app.task()
def sync_importation_pending_objects(
    user_id: str, pending_invites: ProjectImportationPendingInvitation
) -> None:
    from import_export import repositories as import_export_repositories

    import_export_repositories.sync_pending_objects(
        user_id=decode_b64str_to_uuid(user_id), pending_invites=pending_invites
    )
