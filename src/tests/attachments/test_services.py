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

from unittest.mock import AsyncMock, patch

from attachments import services
from tests.utils import factories as f
from tests.utils.bad_params import NOT_EXISTING_UUID

#####################################################
# create_attachment
#####################################################


async def test_create_attachment():
    story = f.build_story()
    uploadfiles = (f.build_image_uploadfile(),)
    attachment = f.build_attachment()

    with (
        patch(
            "attachments.services.attachments_repositories", autospec=True
        ) as fake_attachments_repositories,
    ):
        fake_attachments_repositories.create_attachment.return_value = attachment

        data = await services.create_attachment(
            file=uploadfiles,
            created_by=attachment.created_by,
            object=story,
        )

        assert data == attachment
        fake_attachments_repositories.create_attachment.assert_awaited_once_with(
            file=uploadfiles,
            created_by=attachment.created_by,
            object=story,
        )


async def test_create_attachment_and_emit_event_on_create():
    project = f.build_project()
    story = f.build_story(project=project)
    fake_event_on_create = AsyncMock()
    uploadfiles = (f.build_image_uploadfile(),)
    attachment = f.build_attachment()

    with (
        patch(
            "attachments.services.attachments_repositories", autospec=True
        ) as fake_attachments_repositories,
    ):
        fake_attachments_repositories.create_attachment.return_value = attachment

        await services.create_attachment(
            file=uploadfiles,
            created_by=attachment.created_by,
            object=story,
            event_on_create=fake_event_on_create,
        )

        fake_attachments_repositories.create_attachment.assert_awaited_once_with(
            file=uploadfiles,
            created_by=attachment.created_by,
            object=story,
        )
        fake_event_on_create.assert_awaited_once_with(attachment=attachment)


#####################################################
# list_attachments
#####################################################


async def test_list_attachments():
    story = f.build_story(id="")
    attachments = [
        f.build_attachment(),
        f.build_attachment(),
        f.build_attachment(),
    ]

    with (
        patch(
            "attachments.services.attachments_repositories", autospec=True
        ) as fake_attachments_repositories,
        patch(
            "attachments.services.get_contenttype_for_model", autospec=True
        ) as fake_get_contenttype_for_model,
    ):
        fake_attachments_repositories.list_attachments.return_value = attachments
        attachments_list = await services.list_attachments(
            content_object=story,
        )
        fake_attachments_repositories.list_attachments.assert_awaited_once()
        fake_get_contenttype_for_model.assert_awaited_once()
        assert len(attachments_list) == 3


##########################################################
# get_coment
##########################################################


async def test_get_attachment():
    attachment_id = NOT_EXISTING_UUID

    with (
        patch(
            "attachments.services.attachments_repositories", autospec=True
        ) as fake_attachments_repositories,
    ):
        await services.get_attachment(attachment_id=attachment_id)
        fake_attachments_repositories.get_attachment.assert_awaited_once_with(
            filters={"id": attachment_id},
            prefetch_related=["content_object", "content_object__project"],
        )


##########################################################
# delete_coment
##########################################################


async def test_delete_attachment():
    attachment = f.build_attachment(id=NOT_EXISTING_UUID)

    with (
        patch(
            "attachments.services.attachments_repositories", autospec=True
        ) as fake_attachments_repositories,
    ):
        fake_attachments_repositories.delete_attachments.return_value = True

        assert await services.delete_attachment(attachment=attachment)

        fake_attachments_repositories.delete_attachments.assert_awaited_once_with(
            filters={"id": attachment.id},
        )


async def test_delete_attachment_and_emit_event_on_delete():
    attachment = f.build_attachment(id=NOT_EXISTING_UUID)
    fake_event_on_delete = AsyncMock()

    with (
        patch(
            "attachments.services.attachments_repositories", autospec=True
        ) as fake_attachments_repositories,
    ):
        fake_attachments_repositories.delete_attachments.return_value = True

        assert await services.delete_attachment(
            attachment=attachment, event_on_delete=fake_event_on_delete
        )

        fake_attachments_repositories.delete_attachments.assert_awaited_once_with(
            filters={"id": attachment.id},
        )
        fake_event_on_delete.assert_awaited_once_with(attachment=attachment)


async def test_delete_attachment_that_does_not_exist():
    attachment = f.build_attachment(id=NOT_EXISTING_UUID)
    fake_event_on_delete = AsyncMock()

    with (
        patch(
            "attachments.services.attachments_repositories", autospec=True
        ) as fake_attachments_repositories,
    ):
        fake_attachments_repositories.delete_attachments.return_value = False

        assert not await services.delete_attachment(
            attachment=attachment, event_on_delete=fake_event_on_delete
        )

        fake_attachments_repositories.delete_attachments.assert_awaited_once_with(
            filters={"id": attachment.id},
        )
        fake_event_on_delete.assert_not_awaited()
