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

from attachments import repositories
from tests.utils import factories as f

pytestmark = pytest.mark.django_db(transaction=True)


#############################################################
# create_attachments
#############################################################


async def test_create_attachment(project_template):
    project = await f.create_project(project_template)
    story = await f.create_story(project=project)
    user = await f.create_user()
    file = f.build_image_uploadfile(name="test")

    attachment = await repositories.create_attachment(
        file=file,
        created_by=user,
        object=story,
    )

    assert await story.attachments.acount() == 1
    assert attachment.name == file.filename
    assert attachment.content_type == "image/png"
    assert attachment.size == 145


##########################################################
# list_attachments
##########################################################


async def test_list_attachments():
    story1 = await f.create_story()
    story2 = await f.create_story()
    attachment11 = await f.create_attachment(content_object=story1)
    attachment12 = await f.create_attachment(content_object=story1)
    attachment21 = await f.create_attachment(content_object=story2)

    attachments = await repositories.list_attachments()

    assert len(attachments) == 3
    assert attachment12 == attachments[0]
    assert attachment11 == attachments[1]
    assert attachment21 == attachments[2]


async def test_list_attachments_by_content_object():
    story1 = await f.create_story()
    story2 = await f.create_story()
    attachment11 = await f.create_attachment(content_object=story1)
    attachment12 = await f.create_attachment(content_object=story1)
    await f.create_attachment(content_object=story2)

    attachments = await repositories.list_attachments(
        filters={"content_object": story1}
    )

    assert len(attachments) == 2
    assert attachment12 == attachments[0]
    assert attachment11 == attachments[1]


async def test_list_attachments_paginated_by_content_object():
    story1 = await f.create_story()
    story2 = await f.create_story()
    await f.create_attachment(content_object=story1)
    attachment12 = await f.create_attachment(content_object=story1)
    await f.create_attachment(content_object=story2)

    attachments = await repositories.list_attachments(
        filters={"content_object": story1}, offset=0, limit=1
    )

    assert len(attachments) == 1
    assert attachment12 == attachments[0]


##########################################################
# get_attachment
##########################################################


async def tests_get_attachment():
    story1 = await f.create_story()
    story2 = await f.create_story()
    attachment11 = await f.create_attachment(content_object=story1)
    attachment21 = await f.create_attachment(content_object=story2)
    attachment22 = await f.create_attachment(content_object=story2)

    assert (
        await repositories.get_attachment(filters={"id": attachment22.id})
        == attachment22
    )
    assert (
        await repositories.get_attachment(filters={"content_object": story1})
        == attachment11
    )
    assert (
        await repositories.get_attachment(
            filters={"content_object": story1, "id": attachment21.id}
        )
        is None
    )
    assert (
        await repositories.get_attachment(
            filters={"content_object": story1, "id": attachment11.id}
        )
        == attachment11
    )


##########################################################
# delete_attachments
##########################################################


async def tests_delete_attachments():
    story1 = await f.create_story()
    story2 = await f.create_story()
    await f.create_attachment(content_object=story2)
    await f.create_attachment(content_object=story2)

    assert (
        await repositories.delete_attachments(filters={"content_object": story1}) == 0
    )
    assert (
        await repositories.delete_attachments(filters={"content_object": story2}) == 2
    )
