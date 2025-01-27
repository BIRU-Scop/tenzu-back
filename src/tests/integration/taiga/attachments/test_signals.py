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

from attachments import repositories as attachments_repositories
from attachments.models import Attachment
from attachments.signals import mark_attachment_file_to_delete
from tests.utils import factories as f
from tests.utils import signals as signals_utils
from workspaces.workspaces import repositories as workspaces_repositories

pytestmark = pytest.mark.django_db(transaction=True)


def test_mark_attachment_file_to_delete_is_connected():
    assert mark_attachment_file_to_delete in signals_utils.get_receivers_for_model(
        "post_delete", Attachment
    )


async def test_mark_attachment_file_to_delete_when_delete_first_level_related_model():
    story = await f.create_story()
    attachment = await f.create_attachment(content_object=story)
    storaged_object = attachment.storaged_object

    assert storaged_object.deleted_at is None

    assert await attachments_repositories.delete_attachments(
        filters={"id": attachment.id}
    )
    await storaged_object.refresh_from_db()

    assert storaged_object.deleted_at


async def test_mark_attachment_file_to_delete_when_delete_n_level_related_object():
    workspace = await f.create_workspace()
    project1 = await f.create_project(workspace=workspace)
    project2 = await f.create_project(workspace=workspace)
    story1 = await f.create_story(project=project1)
    story2 = await f.create_story(project=project2)
    attachment11 = await f.create_attachment(content_object=story1)
    attachment12 = await f.create_attachment(content_object=story1)
    attachment21 = await f.create_attachment(content_object=story2)

    storaged_object11 = attachment11.storaged_object
    storaged_object12 = attachment12.storaged_object
    storaged_object21 = attachment21.storaged_object

    assert storaged_object11.deleted_at is None
    assert storaged_object12.deleted_at is None
    assert storaged_object21.deleted_at is None

    assert await workspaces_repositories.delete_workspace(workspace_id=workspace.id)

    await storaged_object11.refresh_from_db()
    await storaged_object12.refresh_from_db()
    await storaged_object21.refresh_from_db()

    assert storaged_object11.deleted_at
    assert storaged_object12.deleted_at
    assert storaged_object21.deleted_at
