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

from datetime import timedelta
from uuid import uuid1

import pytest
from asgiref.sync import sync_to_async

from commons.storage import repositories
from commons.storage.models import StoragedObject
from ninja_jwt.utils import aware_utcnow
from tests.utils import factories as f

pytestmark = pytest.mark.django_db


#############################################################
# create_storaged_objects
#############################################################


async def test_create_storaged_object():
    file = f.build_image_file(name="test")

    storaged_object = await repositories.create_storaged_object(
        file=file,
    )

    assert storaged_object.id
    assert (
        len(repositories.list_storaged_objects(filters={"id": storaged_object.id})) == 1
    )


async def test_bulk_create_storaged_objects():
    file = f.build_image_file(name="test")

    storaged_objects = [
        StoragedObject(
            file=file,
        )
    ]

    await repositories.bulk_create_storaged_objects(storaged_objects)
    assert all(storaged_object.pk for storaged_object in storaged_objects)


##########################################################
# list_storaged_objects
##########################################################


def test_list_storage_objects():
    storaged_object1 = f.StoragedObjectFactory.create()
    storaged_object2 = f.StoragedObjectFactory.create(
        deleted_at=aware_utcnow() - timedelta(days=3)
    )

    assert repositories.list_storaged_objects() == [
        storaged_object2,
        storaged_object1,
    ]


def test_list_storage_objects_filters_by_id():
    storaged_object1 = f.StoragedObjectFactory.create()
    f.StoragedObjectFactory.create(deleted_at=aware_utcnow() - timedelta(days=3))

    assert repositories.list_storaged_objects(filters={"id": uuid1()}) == []
    assert repositories.list_storaged_objects(filters={"id": storaged_object1.id}) == [
        storaged_object1
    ]


def test_list_storage_objects_filters_by_deleted_datetime():
    f.StoragedObjectFactory.create()
    storaged_object2 = f.StoragedObjectFactory.create(
        deleted_at=aware_utcnow() - timedelta(days=3)
    )

    assert (
        repositories.list_storaged_objects(
            filters={"deleted_at__lt": aware_utcnow() - timedelta(days=4)}
        )
        == []
    )
    assert repositories.list_storaged_objects(
        filters={"deleted_at__lt": aware_utcnow() - timedelta(days=2)}
    ) == [storaged_object2]


##########################################################
# delete_storaged_object
##########################################################


def test_delete_storaged_object():
    storaged_object = f.StoragedObjectFactory.create()
    file_path = storaged_object.file.path
    storage = storaged_object.file.storage

    assert len(repositories.list_storaged_objects()) == 1
    assert storage.exists(file_path)

    repositories.delete_storaged_object(storaged_object=storaged_object)

    assert len(repositories.list_storaged_objects()) == 0
    assert not storage.exists(file_path)


def test_delete_storaged_object_that_has_been_used():
    storaged_object = f.StoragedObjectFactory.create()
    file_path = storaged_object.file.path
    storage = storaged_object.file.storage

    story = f.StoryFactory.create()
    f.AttachmentFactory.create(content_object=story, storaged_object=storaged_object)

    assert len(repositories.list_storaged_objects()) == 1
    assert storage.exists(file_path)

    assert not repositories.delete_storaged_object(storaged_object=storaged_object)

    assert len(repositories.list_storaged_objects()) == 1
    assert storage.exists(file_path)


##########################################################
# mark_storaged_object_as_deleted
##########################################################


def test_mark_storaged_object_as_deleted():
    storaged_object = f.StoragedObjectFactory.create()

    assert not storaged_object.deleted_at
    repositories.mark_storaged_object_as_deleted(storaged_object=storaged_object)
    assert storaged_object.deleted_at
