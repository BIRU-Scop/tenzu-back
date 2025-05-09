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

from unittest.mock import AsyncMock, PropertyMock, patch
from uuid import uuid1

from base.utils.datetime import aware_utcnow
from comments import services
from tests.utils import factories as f

#####################################################
# create_comment
#####################################################


async def test_create_comment():
    story = f.build_story()
    comment = f.build_comment()

    with (
        patch(
            "comments.services.comments_repositories", autospec=True
        ) as fake_comments_repositories,
    ):
        fake_comments_repositories.create_comment.return_value = comment

        await services.create_comment(
            content_object=story,
            text=comment.text,
            created_by=comment.created_by,
        )

        fake_comments_repositories.create_comment.assert_awaited_once_with(
            content_object=story,
            text=comment.text,
            created_by=comment.created_by,
        )


async def test_create_comment_and_emit_event_on_creation():
    project = f.build_project()
    story = f.build_story(project=project)
    fake_event_on_create = AsyncMock()
    comment = f.build_comment()

    with (
        patch(
            "comments.services.comments_repositories", autospec=True
        ) as fake_comments_repositories,
        patch(
            "comments.models.Comment.project",
            new_callable=PropertyMock,
            return_value=project,
        ),
    ):
        fake_comments_repositories.create_comment.return_value = comment

        await services.create_comment(
            content_object=story,
            text=comment.text,
            created_by=comment.created_by,
            event_on_create=fake_event_on_create,
        )

        fake_comments_repositories.create_comment.assert_awaited_once_with(
            content_object=story,
            text=comment.text,
            created_by=comment.created_by,
        )
        fake_event_on_create.assert_awaited_once_with(comment=comment)


async def test_create_comment_and_notify_on_creation():
    project = f.build_project()
    story = f.build_story(project=project)
    fake_notification_on_create = AsyncMock()
    comment = f.build_comment()

    with (
        patch(
            "comments.services.comments_repositories", autospec=True
        ) as fake_comments_repositories,
        patch(
            "comments.models.Comment.project",
            new_callable=PropertyMock,
            return_value=project,
        ),
    ):
        fake_comments_repositories.create_comment.return_value = comment

        await services.create_comment(
            content_object=story,
            text=comment.text,
            created_by=comment.created_by,
            notification_on_create=fake_notification_on_create,
        )

        fake_comments_repositories.create_comment.assert_awaited_once_with(
            content_object=story,
            text=comment.text,
            created_by=comment.created_by,
        )
        fake_notification_on_create.assert_awaited_once_with(
            comment=comment, emitted_by=comment.created_by
        )


#####################################################
# list_comments
#####################################################


async def test_list_comments():
    story = f.build_story(id="")
    comments = [
        f.build_comment(),
        f.build_comment(deleted_by=story.created_by),
        f.build_comment(),
    ]

    filters = {"content_object": story}
    select_related = ["created_by", "deleted_by"]
    order_by = ["-created_at"]
    offset = 0
    limit = 100
    total = 3
    total_objs = 2

    with (
        patch(
            "comments.services.comments_repositories", autospec=True
        ) as fake_comments_repositories,
    ):
        fake_comments_repositories.list_comments.return_value = comments
        fake_comments_repositories.get_total_comments.side_effect = [total, total_objs]
        (
            pagination,
            total_comments,
            comments_list,
        ) = await services.list_paginated_comments(
            content_object=story, order_by=order_by, offset=offset, limit=limit
        )
        fake_comments_repositories.list_comments.assert_awaited_once_with(
            filters=filters,
            select_related=select_related,
            order_by=order_by,
            offset=offset,
            limit=limit,
        )
        fake_comments_repositories.get_total_comments.assert_awaited()
        assert len(comments_list) == 3
        assert pagination.offset == offset
        assert pagination.limit == limit


##########################################################
# get_coment
##########################################################


async def test_get_comment():
    story = f.build_story(id="story_id")
    comment_id = uuid1()

    with (
        patch(
            "comments.services.comments_repositories", autospec=True
        ) as fake_comments_repositories,
    ):
        await services.get_comment(comment_id=comment_id)
        fake_comments_repositories.get_comment.assert_awaited_once_with(
            filters={"id": comment_id},
            select_related=["created_by", "deleted_by"],
            prefetch_related=["content_object", "project", "workspace"],
            excludes={"deleted": True},
        )


##########################################################
# update_coment
##########################################################


async def test_update_comment():
    story = f.build_story()
    comment = f.build_comment()
    updated_text = "Updated text"

    with (
        patch(
            "comments.services.comments_repositories", autospec=True
        ) as fake_comments_repositories,
    ):
        fake_comments_repositories.update_comment.return_value = comment

        await services.update_comment(comment=comment, values={"text": updated_text})

        fake_comments_repositories.update_comment.assert_awaited_once_with(
            comment=comment, values={"text": updated_text}
        )


async def test_update_comment_and_emit_event_on_update():
    project = f.build_project()
    story = f.build_story(project=project)
    comment = f.build_comment()
    updated_text = "Updated text"
    fake_event_on_update = AsyncMock()

    with (
        patch(
            "comments.services.comments_repositories", autospec=True
        ) as fake_comments_repositories,
        patch(
            "comments.models.Comment.project",
            new_callable=PropertyMock,
            return_value=project,
        ),
    ):
        fake_comments_repositories.update_comment.return_value = comment

        await services.update_comment(
            comment=comment,
            values={"text": updated_text},
            event_on_update=fake_event_on_update,
        )

        fake_comments_repositories.update_comment.assert_awaited_once_with(
            comment=comment, values={"text": updated_text}
        )

        fake_event_on_update.assert_awaited_once_with(comment=comment)


##########################################################
# delete_coment
##########################################################


async def test_delete_comment():
    now = aware_utcnow()
    comment = f.build_comment()
    updated_comment = f.build_comment(
        id=comment.id, text="", deleted_by=comment.created_by, deleted_at=now
    )

    with (
        patch(
            "comments.services.comments_repositories", autospec=True
        ) as fake_comments_repositories,
        patch("comments.services.aware_utcnow", autospec=True) as fake_aware_utcnow,
    ):
        fake_aware_utcnow.return_value = now
        fake_comments_repositories.update_comment.return_value = updated_comment

        assert (
            await services.delete_comment(
                comment=comment, deleted_by=comment.created_by
            )
            == updated_comment
        )

        fake_comments_repositories.update_comment.assert_awaited_once_with(
            comment=comment,
            values={
                "text": updated_comment.text,
                "deleted_by": updated_comment.deleted_by,
                "deleted_at": updated_comment.deleted_at,
            },
        )


async def test_delete_comment_and_emit_event_on_delete():
    now = aware_utcnow()
    comment = f.build_comment()
    updated_comment = f.build_comment(
        id=comment.id, text="", deleted_by=comment.created_by, deleted_at=now
    )
    fake_event_on_delete = AsyncMock()

    with (
        patch(
            "comments.services.comments_repositories", autospec=True
        ) as fake_comments_repositories,
        patch("comments.services.aware_utcnow", autospec=True) as fake_aware_utcnow,
    ):
        fake_aware_utcnow.return_value = now
        fake_comments_repositories.update_comment.return_value = updated_comment

        assert (
            await services.delete_comment(
                comment=comment,
                deleted_by=comment.created_by,
                event_on_delete=fake_event_on_delete,
            )
            == updated_comment
        )

        fake_comments_repositories.update_comment.assert_awaited_once_with(
            comment=comment,
            values={
                "text": updated_comment.text,
                "deleted_by": updated_comment.deleted_by,
                "deleted_at": updated_comment.deleted_at,
            },
        )
        fake_event_on_delete.assert_awaited_once_with(comment=updated_comment)
