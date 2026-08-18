# -*- coding: utf-8 -*-
# Copyright (C) 2026 BIRU
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
from django.test import override_settings

from base.utils.uuid import encode_uuid_to_b64str
from commons.colors import NUM_COLORS
from permissions.choices import ProjectPermissions
from stories.tags.models import StoryTag, StoryTagAssignment
from tests.utils import factories as f
from tests.utils.bad_params import NOT_EXISTING_REF

pytestmark = pytest.mark.django_db


##########################################################
# POST /projects/<id>/tags
##########################################################


async def test_create_story_tag_ok(client, project_template):
    project = await f.create_project(project_template)
    data = {"label": "Bug", "color": 3}

    client.login(project.created_by)
    response = await client.post(f"/projects/{project.b64id}/stories/tags", json=data)
    assert response.status_code == 200, response.data

    tag = response.data["data"]
    assert tag["id"]
    assert tag["label"] == "Bug"
    assert tag["color"] == 3
    assert tag["storiesCount"] == 0


async def test_create_story_tag_invalid_payload(client, project_template):
    project = await f.create_project(project_template)
    client.login(project.created_by)

    invalid_payloads = [
        {"label": "Bug"},
        {"color": 1},
        {"label": "Bug", "color": 0},
        {"label": "Bug", "color": NUM_COLORS + 1},
        {"label": "", "color": 1},
        {"label": "   ", "color": 1},
        {"label": "x" * 51, "color": 1},
        {"label": "Bug\x00", "color": 1},
        {"label": "Bug‮txt", "color": 1},
    ]
    for data in invalid_payloads:
        response = await client.post(
            f"/projects/{project.b64id}/stories/tags", json=data
        )
        assert response.status_code == 422, (data, response.data)

    response = await client.post(
        f"/projects/{project.b64id}/stories/tags", json={"label": "  Bug  ", "color": 1}
    )
    assert response.status_code == 200, response.data
    assert response.data["data"]["label"] == "Bug"


async def test_create_story_tag_duplicated_label_case_insensitive(
    client, project_template
):
    project = await f.create_project(project_template)
    await f.create_story_tag(project=project, label="Bug")

    client.login(project.created_by)
    response = await client.post(
        f"/projects/{project.b64id}/stories/tags", json={"label": "bug", "color": 1}
    )
    assert response.status_code == 400, response.data
    assert response.data["error"]["detail"] == "story-tag-label-already-exists"


async def test_create_story_tag_normalizes_label_to_nfc(client, project_template):
    project = await f.create_project(project_template)
    await f.create_story_tag(project=project, label="Caf\u00e9")  # NFC "Café"

    client.login(project.created_by)
    response = await client.post(
        f"/projects/{project.b64id}/stories/tags",
        json={"label": "Cafe\u0301", "color": 1},
    )
    assert response.status_code == 400, response.data
    assert response.data["error"]["detail"] == "story-tag-label-already-exists"


async def test_create_story_tag_max_per_project_reached(client, project_template):
    project = await f.create_project(project_template)
    await f.create_story_tag(project=project, label="Bug")
    await f.create_story_tag(project=project, label="Feature")

    client.login(project.created_by)
    with override_settings(**{"MAX_STORY_TAGS_PER_PROJECT": 2}):
        response = await client.post(
            f"/projects/{project.b64id}/stories/tags", json={"label": "Doc", "color": 1}
        )
    assert response.status_code == 400, response.data
    assert response.data["error"]["detail"] == "max-story-tags-per-project-reached"


async def test_create_story_tag_user_without_permissions(client, project_template):
    project = await f.create_project(project_template)
    data = {"label": "Bug", "color": 1}

    response = await client.post(f"/projects/{project.b64id}/stories/tags", json=data)
    assert response.status_code == 401, response.data

    pj_member = await f.create_user()
    pj_role = await f.create_project_role(
        permissions=[
            ProjectPermissions.VIEW_STORY.value,
            ProjectPermissions.MODIFY_STORY.value,
        ],
        is_owner=False,
        project=project,
    )
    await f.create_project_membership(user=pj_member, project=project, role=pj_role)

    client.login(pj_member)
    response = await client.post(f"/projects/{project.b64id}/stories/tags", json=data)
    assert response.status_code == 403, response.data


##########################################################
# PATCH /projects/<id>/tags/<tag_id>
##########################################################


async def test_update_story_tag_ok(client, project_template):
    project = await f.create_project(project_template)
    story_tag = await f.create_story_tag(project=project, label="Bug", color=1)
    story = await f.create_story(project=project)
    await f.create_story_tag_assignment(tag=story_tag, story=story)

    client.login(project.created_by)
    response = await client.patch(
        f"/stories/tags/{story_tag.b64id}",
        json={"label": "Feature", "color": 5},
    )
    assert response.status_code == 200, response.data
    assert response.data["data"]["label"] == "Feature"
    assert response.data["data"]["color"] == 5
    assert response.data["data"]["storiesCount"] == 1


async def test_update_story_tag_duplicated_label_case_insensitive(
    client, project_template
):
    project = await f.create_project(project_template)
    await f.create_story_tag(project=project, label="Bug")
    story_tag = await f.create_story_tag(project=project, label="Feature")

    client.login(project.created_by)
    response = await client.patch(
        f"/stories/tags/{story_tag.b64id}",
        json={"label": "bug", "color": 2},
    )
    assert response.status_code == 400, response.data
    assert response.data["error"]["detail"] == "story-tag-label-already-exists"


async def test_update_story_tag_own_label_case_change(client, project_template):
    project = await f.create_project(project_template)
    story_tag = await f.create_story_tag(project=project, label="bug")

    client.login(project.created_by)
    response = await client.patch(
        f"/stories/tags/{story_tag.b64id}",
        json={"label": "Bug", "color": 2},
    )
    assert response.status_code == 200, response.data
    assert response.data["data"]["label"] == "Bug"


async def test_update_story_tag_user_without_permissions(client, project_template):
    project = await f.create_project(project_template)
    story_tag = await f.create_story_tag(project=project, label="Bug")
    data = {"label": "Feature", "color": 2}

    response = await client.patch(f"/stories/tags/{story_tag.b64id}", json=data)
    assert response.status_code == 401, response.data

    pj_member = await f.create_user()
    pj_role = await f.create_project_role(
        permissions=[ProjectPermissions.VIEW_STORY.value],
        is_owner=False,
        project=project,
    )
    await f.create_project_membership(user=pj_member, project=project, role=pj_role)

    client.login(pj_member)
    response = await client.patch(f"/stories/tags/{story_tag.b64id}", json=data)
    assert response.status_code == 403, response.data


##########################################################
# DELETE /projects/<id>/tags/<tag_id>
##########################################################


async def test_delete_story_tag_ok(client, project_template):
    project = await f.create_project(project_template)
    story_tag = await f.create_story_tag(project=project, label="Bug")
    story = await f.create_story(project=project)
    await f.create_story_tag_assignment(tag=story_tag, story=story)

    client.login(project.created_by)
    response = await client.delete(f"/stories/tags/{story_tag.b64id}")
    assert response.status_code == 204, response.data

    response = await client.get(f"/projects/{project.b64id}/stories/tags")
    assert response.data["data"] == []


async def test_delete_story_tag_user_without_permissions(client, project_template):
    project = await f.create_project(project_template)
    story_tag = await f.create_story_tag(project=project, label="Bug")

    response = await client.delete(f"/stories/tags/{story_tag.b64id}")
    assert response.status_code == 401, response.data

    pj_member = await f.create_user()
    pj_role = await f.create_project_role(
        permissions=[ProjectPermissions.VIEW_STORY.value],
        is_owner=False,
        project=project,
    )
    await f.create_project_membership(user=pj_member, project=project, role=pj_role)

    client.login(pj_member)
    response = await client.delete(f"/stories/tags/{story_tag.b64id}")
    assert response.status_code == 403, response.data


##########################################################
# POST /projects/<id>/stories/<ref>/tags
##########################################################


async def test_create_story_tag_assignment_ok(client, project_template):
    project = await f.create_project(project_template)
    story = await f.create_story(project=project)
    story_tag = await f.create_story_tag(project=project, label="Bug")
    data = {"tag_id": story_tag.b64id}

    client.login(project.created_by)
    response = await client.post(
        f"/projects/{project.b64id}/stories/{story.ref}/tags", json=data
    )
    assert response.status_code == 200, response.data
    assert response.data["data"]["tag"]["id"] == story_tag.b64id
    assert response.data["data"]["tag"]["storiesCount"] == 1
    assert response.data["data"]["story"]["ref"] == story.ref

    response = await client.post(
        f"/projects/{project.b64id}/stories/{story.ref}/tags", json=data
    )
    assert response.status_code == 200, response.data
    assert (
        await StoryTagAssignment.objects.filter(story=story, tag=story_tag).acount()
        == 1
    )


async def test_create_story_tag_assignment_cross_project_bad_request(
    client, project_template
):
    project = await f.create_project(project_template)
    story = await f.create_story(project=project)
    other_project_tag = await f.create_story_tag(label="Bug")

    client.login(project.created_by)
    response = await client.post(
        f"/projects/{project.b64id}/stories/{story.ref}/tags",
        json={"tag_id": other_project_tag.b64id},
    )
    assert response.status_code == 400, response.data


async def test_create_story_tag_assignment_story_not_found(client, project_template):
    project = await f.create_project(project_template)
    story_tag = await f.create_story_tag(project=project, label="Bug")

    client.login(project.created_by)
    response = await client.post(
        f"/projects/{project.b64id}/stories/{NOT_EXISTING_REF}/tags",
        json={"tag_id": story_tag.b64id},
    )
    assert response.status_code == 404, response.data


async def test_create_story_tag_assignment_user_without_permissions(
    client, project_template
):
    project = await f.create_project(project_template)
    story = await f.create_story(project=project)
    story_tag = await f.create_story_tag(project=project, label="Bug")
    data = {"tag_id": story_tag.b64id}

    response = await client.post(
        f"/projects/{project.b64id}/stories/{story.ref}/tags", json=data
    )
    assert response.status_code == 401, response.data

    pj_member = await f.create_user()
    pj_role = await f.create_project_role(
        permissions=[ProjectPermissions.VIEW_STORY.value],
        is_owner=False,
        project=project,
    )
    await f.create_project_membership(user=pj_member, project=project, role=pj_role)

    client.login(pj_member)
    response = await client.post(
        f"/projects/{project.b64id}/stories/{story.ref}/tags", json=data
    )
    assert response.status_code == 403, response.data


##########################################################
# DELETE /projects/<id>/stories/<ref>/tags/<tag_id>
##########################################################


async def test_delete_story_tag_assignment_ok(client, project_template):
    project = await f.create_project(project_template)
    story = await f.create_story(project=project)
    story_tag = await f.create_story_tag(project=project, label="Bug")
    assignment = await f.create_story_tag_assignment(tag=story_tag, story=story)

    client.login(project.created_by)
    response = await client.delete(
        f"/projects/{project.b64id}/stories/{story.ref}/tags/{story_tag.b64id}"
    )
    assert response.status_code == 204, response.data
    assert not await StoryTagAssignment.objects.filter(id=assignment.id).aexists()
    assert await StoryTag.objects.filter(id=story_tag.id).aexists()


async def test_delete_story_tag_assignment_not_assigned_not_found(
    client, project_template
):
    project = await f.create_project(project_template)
    story = await f.create_story(project=project)
    story_tag = await f.create_story_tag(project=project, label="Bug")

    client.login(project.created_by)
    response = await client.delete(
        f"/projects/{project.b64id}/stories/{story.ref}/tags/{story_tag.b64id}"
    )
    assert response.status_code == 404, response.data


async def test_delete_story_tag_assignment_user_without_permissions(
    client, project_template
):
    project = await f.create_project(project_template)
    story = await f.create_story(project=project)
    story_tag = await f.create_story_tag(project=project, label="Bug")
    await f.create_story_tag_assignment(tag=story_tag, story=story)

    response = await client.delete(
        f"/projects/{project.b64id}/stories/{story.ref}/tags/{story_tag.b64id}"
    )
    assert response.status_code == 401, response.data

    pj_member = await f.create_user()
    pj_role = await f.create_project_role(
        permissions=[ProjectPermissions.VIEW_STORY.value],
        is_owner=False,
        project=project,
    )
    await f.create_project_membership(user=pj_member, project=project, role=pj_role)

    client.login(pj_member)
    response = await client.delete(
        f"/projects/{project.b64id}/stories/{story.ref}/tags/{story_tag.b64id}"
    )
    assert response.status_code == 403, response.data


##########################################################
# GET /projects/<id>/tags
##########################################################


async def test_list_story_tags_with_count_sorted(client, project_template):
    project = await f.create_project(project_template)
    tag_apple = await f.create_story_tag(project=project, label="apple")
    await f.create_story_tag(project=project, label="Zebra")
    await f.create_story_tag(project=project, label="Mango")
    story1 = await f.create_story(project=project)
    story2 = await f.create_story(project=project)
    await f.create_story_tag_assignment(tag=tag_apple, story=story1)
    await f.create_story_tag_assignment(tag=tag_apple, story=story2)

    client.login(project.created_by)
    response = await client.get(f"/projects/{project.b64id}/stories/tags")
    assert response.status_code == 200, response.data

    tags = response.data["data"]
    assert [tag["label"] for tag in tags] == ["apple", "Mango", "Zebra"]
    assert [tag["storiesCount"] for tag in tags] == [2, 0, 0]


async def test_list_story_tags_user_without_permissions(client, project_template):
    project = await f.create_project(project_template)

    response = await client.get(f"/projects/{project.b64id}/stories/tags")
    assert response.status_code == 401, response.data

    pj_member = await f.create_user()
    pj_role = await f.create_project_role(
        permissions=[],
        is_owner=False,
        project=project,
    )
    await f.create_project_membership(user=pj_member, project=project, role=pj_role)

    client.login(pj_member)
    response = await client.get(f"/projects/{project.b64id}/stories/tags")
    assert response.status_code == 403, response.data


async def test_list_story_tags_with_modify_project_but_no_view_story(
    client, project_template
):
    project = await f.create_project(project_template)
    await f.create_story_tag(project=project, label="Bug")
    pj_member = await f.create_user()
    pj_role = await f.create_project_role(
        permissions=[ProjectPermissions.MODIFY_PROJECT.value],
        is_owner=False,
        project=project,
    )
    await f.create_project_membership(user=pj_member, project=project, role=pj_role)

    client.login(pj_member)
    response = await client.get(f"/projects/{project.b64id}/stories/tags")
    assert response.status_code == 200, response.data
    assert [tag["label"] for tag in response.data["data"]] == ["Bug"]
