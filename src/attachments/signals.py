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

from typing import Any

from django.db.models.signals import post_delete
from django.dispatch import receiver

from attachments.models import Attachment
from base.db.models import Model
from commons.storage import repositories as storage_repositories


@receiver(
    post_delete,
    sender=Attachment,
    dispatch_uid="mark_attachment_file_to_delete",
)
def mark_attachment_file_to_delete(
    sender: Model, instance: Attachment, **kwargs: Any
) -> None:
    """
    Mark the store object (with the file) of the attachment as deleted.
    """
    storage_repositories.mark_storaged_object_as_deleted(
        storaged_object=instance.storaged_object
    )
