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

import pytest

from comments import repositories as comments_repositories
from ninja_jwt.utils import aware_utcnow
from permissions.choices import ProjectPermissions
from tests.utils import factories as f
from tests.utils.bad_params import NOT_EXISTING_B64ID, NOT_EXISTING_REF

pytestmark = pytest.mark.django_db


##########################################################
# POST projects/<id>/stories/<ref>/comments
##########################################################


async def test_create_story_comment_ok(client, project_template):
    project = await f.create_project(project_template)
    story = await f.create_story(project=project)

    data = {"text": "<p>Sample comment</p>"}

    client.login(story.project.created_by)
    response = await client.post(
        f"/projects/{story.project.b64id}/stories/{story.ref}/comments", json=data
    )
    assert response.status_code == 200, response.data["data"]

    user = await f.create_user()
    general_member_role = await f.create_project_role(
        permissions=[ProjectPermissions.CREATE_MODIFY_DELETE_COMMENT.value],
        is_owner=False,
        project=project,
    )
    await f.create_project_membership(
        user=user, project=project, role=general_member_role
    )

    client.login(user)
    response = await client.post(
        f"/projects/{story.project.b64id}/stories/{story.ref}/comments", json=data
    )
    assert response.status_code == 200, response.data["data"]


async def test_create_story_comment_forbidden_anonymous(client, project_template):
    project = await f.create_project(project_template)
    story = await f.create_story(project=project)

    data = {"text": "<p>Sample comment</p>"}

    response = await client.post(
        f"/projects/{story.project.b64id}/stories/{story.ref}/comments", json=data
    )
    assert response.status_code == 401, response.data


async def test_create_story_comment_forbidden_not_member(client, project_template):
    project = await f.create_project(project_template)
    story = await f.create_story(project=project)
    user = await f.create_user()

    data = {"text": "<p>Sample comment</p>"}

    client.login(user)
    response = await client.post(
        f"/projects/{story.project.b64id}/stories/{story.ref}/comments", json=data
    )
    assert response.status_code == 403, response.data


async def test_create_story_comment_forbidden_no_permission(client, project_template):
    project = await f.create_project(project_template)
    story = await f.create_story(project=project)
    user = await f.create_user()

    data = {"text": "<p>Sample comment</p>"}

    general_member_role = await f.create_project_role(
        permissions=[],
        is_owner=False,
        project=project,
    )
    await f.create_project_membership(
        user=user, project=project, role=general_member_role
    )

    client.login(user)
    response = await client.post(
        f"/projects/{story.project.b64id}/stories/{story.ref}/comments", json=data
    )
    assert response.status_code == 403, response.data


async def test_create_story_comment_error_nonexistent_project(client):
    user = await f.create_user()
    story = await f.create_story()

    data = {"text": "<p>Sample comment</p>"}

    client.login(user)
    response = await client.post(
        f"/projects/{NOT_EXISTING_B64ID}/stories/{story.ref}/comments", json=data
    )
    assert response.status_code == 404, response.data


async def test_create_story_comment_error_nonexistent_story(client, project_template):
    project = await f.create_project(project_template)

    data = {"text": "<p>Sample comment</p>"}

    client.login(project.created_by)
    response = await client.post(
        f"/projects/{project.b64id}/stories/{NOT_EXISTING_REF}/comments", json=data
    )
    assert response.status_code == 404, response.data


async def test_create_story_comment_error_invalid_form(client, project_template):
    project = await f.create_project(project_template)

    data = {"invalid_param": "<p>Sample comment</p>"}

    client.login(project.created_by)
    response = await client.post(
        f"/projects/{project.b64id}/stories/{NOT_EXISTING_REF}/comments", json=data
    )
    assert response.status_code == 422, response.data


##########################################################
# GET projects/<id>/stories/<ref>/comments
##########################################################


async def test_list_story_comments_ok(client, project_template):
    project = await f.create_project(project_template)
    story = await f.create_story(project=project)
    await f.create_comment(
        content_object=story, created_by=story.project.created_by, text="comment"
    )

    client.login(story.project.created_by)
    response = await client.get(
        f"/projects/{story.project.b64id}/stories/{story.ref}/comments"
    )
    assert response.status_code == 200, response.data["data"]
    res = response.data["data"]
    assert len(res) == 1

    user = await f.create_user()
    general_member_role = await f.create_project_role(
        permissions=[ProjectPermissions.VIEW_COMMENT.value],
        is_owner=False,
        project=project,
    )
    await f.create_project_membership(
        user=user, project=project, role=general_member_role
    )

    client.login(user)
    response = await client.get(
        f"/projects/{story.project.b64id}/stories/{story.ref}/comments"
    )
    assert response.status_code == 200, response.data["data"]
    res = response.data["data"]
    assert len(res) == 1


async def test_list_story_comments_forbidden_anonymous(client, project_template):
    project = await f.create_project(project_template)
    story = await f.create_story(project=project)

    response = await client.get(
        f"/projects/{story.project.b64id}/stories/{story.ref}/comments"
    )
    assert response.status_code == 401, response.data


async def test_list_story_comments_forbidden_not_member(client, project_template):
    project = await f.create_project(project_template)
    story = await f.create_story(project=project)
    user = await f.create_user()

    client.login(user)
    response = await client.get(
        f"/projects/{story.project.b64id}/stories/{story.ref}/comments"
    )
    assert response.status_code == 403, response.data


async def test_list_story_comments_forbidden_no_permission(client, project_template):
    project = await f.create_project(project_template)
    story = await f.create_story(project=project)
    user = await f.create_user()

    general_member_role = await f.create_project_role(
        permissions=[],
        is_owner=False,
        project=project,
    )
    await f.create_project_membership(
        user=user, project=project, role=general_member_role
    )

    client.login(user)
    response = await client.get(
        f"/projects/{story.project.b64id}/stories/{story.ref}/comments"
    )
    assert response.status_code == 403, response.data


async def test_list_story_comments_success_with_custom_pagination(
    client, project_template
):
    project = await f.create_project(project_template)
    story = await f.create_story(project=project)
    await f.create_comment(
        content_object=story, created_by=story.project.created_by, text="comment"
    )

    offset = 0
    limit = 1
    order = "-createdAt"
    query_params = f"offset={offset}&limit={limit}&order={order}"

    client.login(story.project.created_by)
    response = await client.get(
        f"/projects/{story.project.b64id}/stories/{story.ref}/comments?{query_params}"
    )
    assert response.status_code == 200, response.data["data"]
    res = response.data["data"]
    assert len(res) == 1
    assert response.headers["Pagination-Offset"] == "0"
    assert response.headers["Pagination-Limit"] == "1"


async def test_list_story_comments_success_with_deleted_comments(
    client, project_template
):
    project = await f.create_project(project_template)
    story = await f.create_story(project=project)
    await f.create_comment(
        content_object=story, created_by=story.project.created_by, text="comment"
    )
    await f.create_comment(
        content_object=story,
        created_by=story.project.created_by,
        deleted_by=story.project.created_by,
    )

    client.login(story.project.created_by)
    response = await client.get(
        f"/projects/{story.project.b64id}/stories/{story.ref}/comments"
    )
    assert response.status_code == 200, response.data["data"]
    res = response.data["data"]
    assert len(res) == 2


async def test_list_story_comments_error_nonexistent_project(client):
    user = await f.create_user()

    client.login(user)
    response = await client.get(
        f"/projects/{NOT_EXISTING_B64ID}/stories/{NOT_EXISTING_REF}/comments"
    )
    assert response.status_code == 404, response.data


async def test_list_story_comments_error_nonexistent_story(client, project_template):
    project = await f.create_project(project_template)

    client.login(project.created_by)
    response = await client.get(
        f"/projects/{project.b64id}/stories/{NOT_EXISTING_REF}/comments"
    )
    assert response.status_code == 404, response.data


async def test_list_story_comments_error_invalid_order(client, project_template):
    project = await f.create_project(project_template)
    story = await f.create_story(project=project)
    await f.create_comment(
        content_object=story, created_by=story.project.created_by, text="comment"
    )

    order = "-id"
    query_params = f"order={order}"

    client.login(story.project.created_by)
    response = await client.get(
        f"/projects/{story.project.b64id}/stories/{story.ref}/comments?{query_params}"
    )
    assert response.status_code == 422, response.data


##########################################################
# PATCH stories/comments/<id>
##########################################################


async def test_update_story_comment_ok_self(client):
    user = await f.create_user()
    story = await f.create_story()
    comment = await f.create_comment(content_object=story, created_by=user)
    assert comment.modified_at is None
    general_member_role = await f.create_project_role(
        permissions=[ProjectPermissions.CREATE_MODIFY_DELETE_COMMENT.value],
        is_owner=False,
        project=story.project,
    )
    await f.create_project_membership(
        user=user, project=story.project, role=general_member_role
    )

    data = {"text": "Updated comment"}

    client.login(user)
    response = await client.patch(
        f"/stories/comments/{comment.b64id}",
        json=data,
    )
    assert response.status_code == 200, response.data["data"]
    res = response.data["data"]
    assert res["modifiedAt"] is not None


async def test_update_story_comment_ok_moderator(client, project_template):
    project = await f.create_project(project_template)
    story = await f.create_story(project=project, created_by=project.created_by)
    comment = await f.create_comment(content_object=story)

    data = {"text": "Updated comment"}

    user = await f.create_user()
    moderator_member_role = await f.create_project_role(
        permissions=[ProjectPermissions.MODERATE_COMMENT.value],
        is_owner=False,
        project=project,
    )
    await f.create_project_membership(
        user=user, project=project, role=moderator_member_role
    )

    client.login(user)
    response = await client.patch(
        f"/stories/comments/{comment.b64id}",
        json=data,
    )
    assert response.status_code == 200, response.data["data"]


async def test_update_story_comment_error_forbidden_anonymous(client, project_template):
    project = await f.create_project(project_template)
    story = await f.create_story(project=project, created_by=project.created_by)
    comment = await f.create_comment(content_object=story, created_by=story.created_by)

    data = {"text": "Updated comment"}

    response = await client.patch(
        f"/stories/comments/{comment.b64id}",
        json=data,
    )
    assert response.status_code == 401, response.data


async def test_update_story_comment_error_forbidden_not_member(
    client, project_template
):
    project = await f.create_project(project_template)
    story = await f.create_story(project=project, created_by=project.created_by)
    comment = await f.create_comment(content_object=story, created_by=story.created_by)
    user = await f.create_user()

    data = {"text": "Updated comment"}

    client.login(user)
    response = await client.patch(
        f"/stories/comments/{comment.b64id}",
        json=data,
    )
    assert response.status_code == 403, response.data


async def test_update_story_comment_error_forbidden_no_permission(
    client, project_template
):
    project = await f.create_project(project_template)
    story = await f.create_story(project=project, created_by=project.created_by)
    comment = await f.create_comment(content_object=story, created_by=story.created_by)
    user = await f.create_user()

    general_member_role = await f.create_project_role(
        permissions=[],
        is_owner=False,
        project=project,
    )
    await f.create_project_membership(
        user=user, project=project, role=general_member_role
    )

    data = {"text": "Updated comment"}

    client.login(user)
    response = await client.patch(
        f"/stories/comments/{comment.b64id}",
        json=data,
    )
    assert response.status_code == 403, response.data


async def test_update_story_comment_error_forbidden_no_permission_self(client):
    user = await f.create_user()
    story = await f.create_story()
    comment = await f.create_comment(content_object=story, created_by=user)

    general_member_role = await f.create_project_role(
        permissions=[],
        is_owner=False,
        project=story.project,
    )
    await f.create_project_membership(
        user=user, project=story.project, role=general_member_role
    )

    data = {"text": "Updated comment"}

    client.login(user)
    response = await client.patch(
        f"/stories/comments/{comment.b64id}",
        json=data,
    )
    assert response.status_code == 403, response.data


async def test_update_story_comments_404_not_story_comment(client):
    user = await f.create_user()
    workflow = await f.create_workflow()
    comment = await f.create_comment(content_object=workflow, created_by=user)

    data = {"text": "Updated comment"}

    client.login(user)
    response = await client.patch(
        f"/stories/comments/{comment.b64id}",
        json=data,
    )
    assert response.status_code == 404, response.data


async def test_update_story_comment_error_nonexistent_comment(client):
    data = {"text": "Updated comment"}

    client.login(await f.create_user())
    response = await client.patch(
        f"/stories/comments/{NOT_EXISTING_B64ID}",
        json=data,
    )
    assert response.status_code == 404, response.data


async def test_update_story_comment_error_deleted_comment(client, project_template):
    project = await f.create_project(project_template)
    story = await f.create_story(project=project, created_by=project.created_by)
    comment = await f.create_comment(content_object=story, created_by=story.created_by)
    await comments_repositories.update_comment(
        comment=comment,
        values={
            "text": "",
            "deleted_by": story.created_by,
            "deleted_at": aware_utcnow(),
        },
    )

    data = {"text": "Updated comment"}

    client.login(story.created_by)
    response = await client.patch(
        f"/stories/comments/{comment.b64id}",
        json=data,
    )
    assert response.status_code == 404, response.data


##########################################################
# DELETE /stories/comments/<id>
##########################################################


async def test_delete_story_comment_ok_self(client):
    user = await f.create_user()
    story = await f.create_story()
    comment = await f.create_comment(content_object=story, created_by=user)
    assert comment.deleted_at is None
    general_member_role = await f.create_project_role(
        permissions=[ProjectPermissions.CREATE_MODIFY_DELETE_COMMENT.value],
        is_owner=False,
        project=story.project,
    )
    await f.create_project_membership(
        user=user, project=story.project, role=general_member_role
    )

    client.login(user)
    response = await client.delete(f"/stories/comments/{comment.b64id}")
    assert response.status_code == 200, response.data["data"]
    res = response.data["data"]
    assert res["text"] == ""
    assert res["modifiedAt"] is None
    assert res["deletedAt"] is not None


async def test_delete_story_comment_ok_moderator(client, project_template):
    project = await f.create_project(project_template)
    story = await f.create_story(project=project, created_by=project.created_by)
    comment = await f.create_comment(content_object=story)
    assert comment.deleted_at is None

    user = await f.create_user()
    general_member_role = await f.create_project_role(
        permissions=[ProjectPermissions.MODERATE_COMMENT.value],
        is_owner=False,
        project=project,
    )
    await f.create_project_membership(
        user=user, project=project, role=general_member_role
    )

    client.login(user)
    response = await client.delete(f"/stories/comments/{comment.b64id}")
    assert response.status_code == 200, response.data["data"]
    res = response.data["data"]
    assert res["text"] == ""
    assert res["modifiedAt"] is None
    assert res["deletedAt"] is not None


async def test_delete_story_comment_error_forbidden_anonymous(client, project_template):
    project = await f.create_project(project_template)
    story = await f.create_story(project=project, created_by=project.created_by)
    comment = await f.create_comment(content_object=story, created_by=story.created_by)

    response = await client.delete(f"/stories/comments/{comment.b64id}")
    assert response.status_code == 401, response.data


async def test_delete_story_comment_error_forbidden_not_member(
    client, project_template
):
    project = await f.create_project(project_template)
    story = await f.create_story(project=project, created_by=project.created_by)
    comment = await f.create_comment(content_object=story, created_by=story.created_by)
    user = await f.create_user()

    client.login(user)
    response = await client.delete(f"/stories/comments/{comment.b64id}")
    assert response.status_code == 403, response.data


async def test_delete_story_comment_error_forbidden_no_permission(
    client, project_template
):
    project = await f.create_project(project_template)
    story = await f.create_story(project=project, created_by=project.created_by)
    comment = await f.create_comment(content_object=story, created_by=story.created_by)
    user = await f.create_user()

    general_member_role = await f.create_project_role(
        permissions=[],
        is_owner=False,
        project=project,
    )
    await f.create_project_membership(
        user=user, project=project, role=general_member_role
    )

    client.login(user)
    response = await client.delete(f"/stories/comments/{comment.b64id}")
    assert response.status_code == 403, response.data


async def test_delete_story_comment_error_forbidden_no_permission_self(client):
    user = await f.create_user()
    story = await f.create_story()
    comment = await f.create_comment(content_object=story, created_by=user)

    general_member_role = await f.create_project_role(
        permissions=[],
        is_owner=False,
        project=story.project,
    )
    await f.create_project_membership(
        user=user, project=story.project, role=general_member_role
    )

    client.login(user)
    response = await client.delete(f"/stories/comments/{comment.b64id}")
    assert response.status_code == 403, response.data


async def test_delete_story_comment_error_deleted_comment(client, project_template):
    project = await f.create_project(project_template)
    admin_user = project.created_by
    owner_user = await f.create_user()
    story = await f.create_story(project=project)
    comment = await f.create_comment(
        content_object=story, created_by=owner_user, text="comment"
    )
    await comments_repositories.update_comment(
        comment=comment,
        values={
            "text": "",
            "deleted_by": owner_user,
            "deleted_at": aware_utcnow(),
        },
    )

    assert (
        await comments_repositories.get_comment(filters={"id": comment.id}) == comment
    )
    client.login(admin_user)
    response = await client.delete(f"/stories/comments/{comment.b64id}")
    assert response.status_code == 404, response.data


async def test_delete_story_comments_404_not_story_comment(client):
    user = await f.create_user()
    workflow = await f.create_workflow()
    comment = await f.create_comment(content_object=workflow, created_by=user)

    client.login(user)
    response = await client.delete(f"/stories/comments/{comment.b64id}")
    assert response.status_code == 404, response.data


async def test_delete_story_comments_404_not_found_nonexistent_comment(client):
    user = await f.create_user()
    client.login(user)
    response = await client.delete(f"/stories/comments/{NOT_EXISTING_B64ID}")
    assert response.status_code == 404, response.data
