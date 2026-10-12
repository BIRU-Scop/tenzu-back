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
from functools import partial
from typing import Any

from django.db import transaction
from django.db.models import Model
from django.db.models.signals import post_delete
from django.dispatch import receiver

from import_export.models import ProjectImportation


@receiver(
    post_delete,
    sender=ProjectImportation,
    dispatch_uid="delete_importation_source_file",
)
def delete_importation_source_file(
    sender: Model, instance: ProjectImportation, **kwargs: Any
) -> None:
    transaction.on_commit(partial(instance.source.delete, save=False))
