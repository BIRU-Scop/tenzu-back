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
from asgiref.sync import sync_to_async

from permissions.choices import ProjectPermissions
from tests.utils import factories as f
from tests.utils.bad_params import (
    INVALID_B64ID,
    INVALID_REF,
    NOT_EXISTING_B64ID,
    NOT_EXISTING_REF,
    NOT_EXISTING_SLUG,
)

pytestmark = pytest.mark.django_db


##########################################################
# POST /projects/<slug>/workflows/<slug>/stories
##########################################################


async def test_create_story_200_ok_being_ws_or_pj_admin_ok(client, project_template):
    workspace = await f.create_workspace()
    project = await f.create_project(template=project_template, workspace=workspace)
    workflow = await f.create_workflow(project=project)
    workflow_status = await f.create_workflow_status(workflow=workflow)

    data = {
        "title": "New story",
        "description": "Story description",
        "statusId": workflow_status.b64id,
    }

    client.login(workspace.created_by)
    response = await client.post(
        f"/projects/{project.b64id}/workflows/{workflow.slug}/stories", json=data
    )
    assert response.status_code == 200, response.data

    client.login(project.created_by)
    response = await client.post(
        f"/projects/{project.b64id}/workflows/{workflow.slug}/stories", json=data
    )
    assert response.status_code == 200, response.data


async def test_create_story_200_ok_user_has_valid_perm_ok(client, project_template):
    ws_member = await f.create_user()
    pj_member = await f.create_user()
    public_user = await f.create_user()

    workspace = await f.create_workspace()
    await f.create_workspace_membership(user=ws_member, workspace=workspace)

    project = await f.create_project(
        template=project_template,
        workspace=workspace,
    )
    pj_role = await f.create_project_role(
        permissions=ProjectPermissions.values, is_owner=False, project=project
    )
    await f.create_project_membership(user=pj_member, project=project, role=pj_role)

    workflow = await f.create_workflow(project=project)
    workflow_status = await f.create_workflow_status(workflow=workflow)

    data = {
        "title": "New story",
        "description": "Story description",
        "statusId": workflow_status.b64id,
    }

    client.login(ws_member)
    response = await client.post(
        f"/projects/{project.b64id}/workflows/{workflow.slug}/stories", json=data
    )
    assert response.status_code == 200, response.data

    client.login(pj_member)
    response = await client.post(
        f"/projects/{project.b64id}/workflows/{workflow.slug}/stories", json=data
    )
    assert response.status_code == 200, response.data

    client.login(public_user)
    response = await client.post(
        f"/projects/{project.b64id}/workflows/{workflow.slug}/stories", json=data
    )
    assert response.status_code == 200, response.data


async def test_create_story_400_bad_request_invalid_status(client, project_template):
    project = await f.create_project(project_template)
    workflow = await f.create_workflow(project=project)
    await f.create_workflow_status(workflow=workflow)

    data = {"title": "New story", "statusId": NOT_EXISTING_B64ID}

    client.login(project.created_by)
    response = await client.post(
        f"/projects/{project.b64id}/workflows/{workflow.slug}/stories", json=data
    )

    assert response.status_code == 400, response.data


async def test_create_story_403_forbidden_user_has_not_valid_perm(
    client, project_template
):
    ws_member = await f.create_user()
    pj_member = await f.create_user()
    public_user = await f.create_user()

    workspace = await f.create_workspace()
    await f.create_workspace_membership(user=ws_member, workspace=workspace)

    project = await f.create_project(
        template=project_template,
        workspace=workspace,
    )
    NO_ADD_STORY_PERMISSIONS = list(
        set(ProjectPermissions.values) - {ProjectPermissions.CREATE_STORY.value}
    )
    pj_role = await f.create_project_role(
        permissions=NO_ADD_STORY_PERMISSIONS, is_owner=False, project=project
    )
    await f.create_project_membership(user=pj_member, project=project, role=pj_role)

    workflow = await f.create_workflow(project=project)
    workflow_status = await f.create_workflow_status(workflow=workflow)

    data = {"title": "New story", "statusId": workflow_status.b64id}

    client.login(pj_member)
    response = await client.post(
        f"/projects/{project.b64id}/workflows/{workflow.slug}/stories", json=data
    )
    assert response.status_code == 403, response.data

    client.login(public_user)
    response = await client.post(
        f"/projects/{project.b64id}/workflows/{workflow.slug}/stories", json=data
    )
    assert response.status_code == 403, response.data


async def test_create_story_404_project_b64_id(client, project_template):
    project = await f.create_project(project_template)
    workflow = await f.create_workflow(project=project)
    workflow_status = await f.create_workflow_status(workflow=workflow)

    data = {"title": "New story", "statusId": workflow_status.b64id}

    client.login(project.created_by)
    response = await client.post(
        f"/projects/{NOT_EXISTING_B64ID}/workflows/{workflow.slug}/stories", json=data
    )
    assert response.status_code == 404, response.data


async def test_create_story_404_not_found_workflow_slug(client, project_template):
    project = await f.create_project(project_template)
    workflow = await f.create_workflow(project=project)
    workflow_status = await f.create_workflow_status(workflow=workflow)

    data = {"title": "New story", "statusId": workflow_status.b64id}

    client.login(project.created_by)
    response = await client.post(
        f"/projects/{project.b64id}/workflows/{NOT_EXISTING_SLUG}/stories", json=data
    )
    assert response.status_code == 404, response.data


async def test_create_story_422_unprocessable_project_b64_id(client, project_template):
    project = await f.create_project(project_template)
    workflow = await f.create_workflow(project=project)
    workflow_status = await f.create_workflow_status(workflow=workflow)

    data = {"title": "New story", "statusId": workflow_status.b64id}

    client.login(project.created_by)
    response = await client.post(
        f"/projects/{INVALID_B64ID}/workflows/{workflow.slug}/stories", json=data
    )
    assert response.status_code == 422, response.data


##########################################################
# GET /projects/<slug>/workflows/<slug>/stories
##########################################################


async def test_list_workflow_stories_200_ok(client, project_template):
    project = await f.create_project(project_template)
    workflow = await f.create_workflow(project=project)
    workflow_status = await f.create_workflow_status(workflow=workflow)
    await f.create_story(project=project, workflow=workflow, status=workflow_status)
    await f.create_story(project=project, workflow=workflow, status=workflow_status)

    client.login(project.created_by)
    response = await client.get(
        f"/projects/{project.b64id}/workflows/{workflow.slug}/stories"
    )
    assert response.status_code == 200, response.data
    assert response.json()


async def test_list_workflow_stories_200_ok_with_pagination(client, project_template):
    project = await f.create_project(project_template)
    workflow = await f.create_workflow(project=project)
    workflow_status = await f.create_workflow_status(workflow=workflow)
    await f.create_story(project=project, workflow=workflow, status=workflow_status)
    await f.create_story(project=project, workflow=workflow, status=workflow_status)

    offset = 0
    limit = 1

    client.login(project.created_by)
    response = await client.get(
        f"/projects/{project.b64id}/workflows/{workflow.slug}/stories?offset={offset}&limit={limit}"
    )
    assert response.status_code == 200, response.data
    assert response.json()

    assert len(response.json()) == 1
    assert response.headers["Pagination-Offset"] == "0"
    assert response.headers["Pagination-Limit"] == "1"


async def test_list_workflow_stories_404_not_found_project_b64id(client):
    workflow = await f.create_workflow()
    pj_admin = await f.create_user()

    client.login(pj_admin)
    response = await client.get(
        f"/projects/{NOT_EXISTING_B64ID}/workflows/{workflow.slug}/stories"
    )
    assert response.status_code == 404, response.data


async def test_list_workflow_stories_404_not_found_workflow_slug(
    client, project_template
):
    project = await f.create_project(project_template)
    pj_admin = await f.create_user()

    client.login(pj_admin)
    response = await client.get(
        f"/projects/{project.b64id}/workflows/{NOT_EXISTING_SLUG}/stories"
    )
    assert response.status_code == 404, response.data


async def test_list_workflow_stories_422_unprocessable_project_b64id(client):
    workflow = await f.create_workflow()
    pj_admin = await f.create_user()

    client.login(pj_admin)
    response = await client.get(
        f"/projects/{INVALID_B64ID}/workflows/{workflow.slug}/stories"
    )
    assert response.status_code == 422, response.data


async def test_list_story_invalid_workflow(client, project_template):
    project = await f.create_project(project_template)

    client.login(project.created_by)
    response = await client.get(
        f"/projects/{project.b64id}/workflows/{NOT_EXISTING_SLUG}/stories"
    )
    assert response.status_code == 404, response.data


##########################################################
# GET /projects/<slug>/stories/<ref>
##########################################################


async def test_get_story_200_ok(client, project_template):
    project = await f.create_project(project_template)
    workflow = await sync_to_async(project.workflows.first)()
    story_status = await sync_to_async(workflow.statuses.first)()
    story = await f.create_story(
        project=project, workflow=workflow, status=story_status
    )

    client.login(project.created_by)
    response = await client.get(f"/projects/{project.b64id}/stories/{story.ref}")
    res = response.json()

    assert response.status_code == 200, response.data
    assert res["ref"] == story.ref


async def test_get_story_404_not_found_project_b64id(client, project_template):
    project = await f.create_project(project_template)
    story = await f.create_story(project=project)

    client.login(project.created_by)
    response = await client.get(f"/projects/{NOT_EXISTING_B64ID}/stories/{story.ref}")

    assert response.status_code == 404, response.data


async def test_get_story_404_not_found_story_ref(client, project_template):
    project = await f.create_project(project_template)

    client.login(project.created_by)
    response = await client.get(f"/projects/{project.b64id}/stories/{NOT_EXISTING_REF}")

    assert response.status_code == 404, response.data


async def test_get_story_422_unprocessable_project_b64id(client):
    pj_admin = await f.create_user()

    client.login(pj_admin)
    response = await client.get(
        f"/projects/{INVALID_B64ID}/stories/{NOT_EXISTING_B64ID}"
    )

    assert response.status_code == 422, response.data


async def test_get_story_422_unprocessable_story_ref(client, project_template):
    project = await f.create_project(project_template)

    client.login(project.created_by)
    response = await client.get(f"/projects/{project.b64id}/stories/{INVALID_REF}")

    assert response.status_code == 422, response.data


##########################################################
# PATCH /projects/<slug>/stories/<ref>
##########################################################


async def test_update_story_200_ok_unprotected_attribute_status_ok(
    client, project_template
):
    project = await f.create_project(project_template)
    workflow = await project.workflows.afirst()
    status1 = await workflow.statuses.afirst()
    status2 = await workflow.statuses.alast()
    story = await f.create_story(project=project, workflow=workflow, status=status1)

    data = {"version": story.version, "statusId": status2.b64id}
    client.login(project.created_by)
    response = await client.patch(
        f"/projects/{project.b64id}/stories/{story.ref}", json=data
    )
    assert response.status_code == 200, response.data


async def test_update_story_200_ok_unprotected_attribute_workflow_ok(
    client, project_template
):
    project = await f.create_project(project_template)
    workflow1 = await project.workflows.afirst()
    status1 = await workflow1.statuses.afirst()
    workflow2 = await f.create_workflow(project=project)
    story = await f.create_story(project=project, workflow=workflow1, status=status1)

    data = {"version": story.version, "workflowSlug": workflow2.slug}
    client.login(project.created_by)
    response = await client.patch(
        f"/projects/{project.b64id}/stories/{story.ref}", json=data
    )
    assert response.status_code == 200, response.data


async def test_update_story_200_ok_protected_attribute_ok(client, project_template):
    project = await f.create_project(project_template)
    workflow = await project.workflows.afirst()
    status1 = await workflow.statuses.afirst()
    story = await f.create_story(project=project, workflow=workflow, status=status1)

    data = {
        "version": story.version,
        "title": "title updated",
        "description": "description updated",
    }
    client.login(project.created_by)
    response = await client.patch(
        f"/projects/{project.b64id}/stories/{story.ref}", json=data
    )
    assert response.status_code == 200, response.text


async def test_update_story_protected_400_bad_request_attribute_error_with_invalid_version(
    client, project_template
):
    project = await f.create_project(project_template)
    workflow = await project.workflows.afirst()
    status1 = await workflow.statuses.afirst()
    story = await f.create_story(
        project=project, workflow=workflow, status=status1, version=2
    )

    data = {"version": story.version - 1, "title": "new title"}
    client.login(project.created_by)
    response = await client.patch(
        f"/projects/{project.b64id}/stories/{story.ref}", json=data
    )
    assert response.status_code == 400, response.text


async def test_update_story_422_unprocessable_project_b64id(client, project_template):
    project = await f.create_project(project_template)
    story = await f.create_story(project=project)

    data = {"version": 1, "title": "new title"}
    client.login(project.created_by)
    response = await client.patch(
        f"/projects/{INVALID_B64ID}/stories/{story.ref}", json=data
    )
    assert response.status_code == 422, response.text


async def test_update_story_422_unprocessable_story_ref(client, project_template):
    project = await f.create_project(project_template)

    data = {"version": 1, "title": "new title"}
    client.login(project.created_by)
    response = await client.patch(
        f"/projects/{project.b64id}/stories/{INVALID_REF}", json=data
    )
    assert response.status_code == 422, response.text


async def test_update_story_422_unprocessable_both_workflow_and_status(
    client, project_template
):
    project = await f.create_project(project_template)
    story = await f.create_story(project=project)

    data = {"version": 1, "workflowSlug": "workflow-slug", "statusId": project.b64id}
    client.login(project.created_by)
    response = await client.patch(
        f"/projects/{project.b64id}/stories/{story.ref}", json=data
    )
    assert response.status_code == 422, response.text


async def test_update_story_404_not_found_project_b64id(client, project_template):
    project = await f.create_project(project_template)
    story = await f.create_story(project=project)

    data = {"version": 1, "title": "new title"}
    client.login(project.created_by)
    response = await client.patch(
        f"/projects/{NOT_EXISTING_B64ID}/stories/{story.ref}", json=data
    )
    assert response.status_code == 404, response.text


async def test_update_story_404_not_found_story_ref(client, project_template):
    project = await f.create_project(project_template)

    data = {"version": 1, "title": "new title"}
    client.login(project.created_by)
    response = await client.patch(
        f"/projects/{project.b64id}/stories/{NOT_EXISTING_REF}", json=data
    )
    assert response.status_code == 404, response.text


##########################################################
# POST /projects/<slug>/workflows/<slug>/stories/reorder
##########################################################


async def test_reorder_stories_with_reorder_ok(client, project_template):
    project = await f.create_project(project_template)
    workflow = await sync_to_async(project.workflows.first)()
    status_new = await sync_to_async(workflow.statuses.first)()
    s1 = await f.create_story(project=project, workflow=workflow, status=status_new)
    await f.create_story(project=project, workflow=workflow, status=status_new)
    s3 = await f.create_story(project=project, workflow=workflow, status=status_new)

    data = {
        "statusId": status_new.b64id,
        "stories": [s1.ref],
        "reorder": {"place": "before", "ref": s3.ref},
    }
    client.login(project.created_by)
    response = await client.post(
        f"/projects/{project.b64id}/workflows/main/stories/reorder", json=data
    )

    assert response.status_code == 200, response.text
    res = response.json()
    assert "statusId" in res
    assert "reorder" in res
    assert "stories" in res
    assert res["stories"] == [s1.ref]


async def test_reorder_stories_without_reorder_ok(client, project_template):
    project = await f.create_project(project_template)
    workflow = await sync_to_async(project.workflows.first)()
    status_new = await sync_to_async(workflow.statuses.first)()
    s1 = await f.create_story(project=project, workflow=workflow, status=status_new)
    await f.create_story(project=project, workflow=workflow, status=status_new)
    await f.create_story(project=project, workflow=workflow, status=status_new)

    data = {"statusId": status_new.b64id, "stories": [s1.ref]}
    client.login(project.created_by)
    response = await client.post(
        f"/projects/{project.b64id}/workflows/main/stories/reorder", json=data
    )

    assert response.status_code == 200, response.text
    res = response.json()
    assert "statusId" in res
    assert "reorder" in res
    assert "stories" in res
    assert res["stories"] == [s1.ref]


##########################################################
# DELETE /projects/<slug>/stories/<ref>
##########################################################


async def test_delete_204_no_content_story(client, project_template):
    project = await f.create_project(project_template)
    story = await f.create_story(project=project)

    client.login(project.created_by)
    response = await client.delete(f"/projects/{project.b64id}/stories/{story.ref}")
    assert response.status_code == 204, response.text


async def test_delete_story_403_forbidden_user_without_permissions(
    client, project_template
):
    project = await f.create_project(project_template)
    story = await f.create_story(project=project)
    user = await f.create_user()

    client.login(user)
    response = await client.delete(f"/projects/{project.b64id}/stories/{story.ref}")
    assert response.status_code == 403, response.text


async def test_delete_story_404_not_found_project_b64id(client, project_template):
    project = await f.create_project(project_template)
    story = await f.create_story(project=project)

    client.login(project.created_by)
    response = await client.delete(
        f"/projects/{NOT_EXISTING_B64ID}/stories/{story.ref}"
    )
    assert response.status_code == 404, response.text


async def test_delete_story_404_not_found_story_ref(client, project_template):
    project = await f.create_project(project_template)

    client.login(project.created_by)
    response = await client.delete(
        f"/projects/{project.b64id}/stories/{NOT_EXISTING_REF}"
    )
    assert response.status_code == 404, response.text


async def test_delete_story_422_unprocessable_project_b64id(client, project_template):
    project = await f.create_project(project_template)

    client.login(project.created_by)
    response = await client.delete(f"/projects/{project.b64id}/stories/{INVALID_B64ID}")
    assert response.status_code == 422, response.text


async def test_delete_story_422_unprocessable_story_ref(client, project_template):
    project = await f.create_project(project_template)

    client.login(project.created_by)
    response = await client.delete(f"/projects/{project.b64id}/stories/{INVALID_REF}")
    assert response.status_code == 422, response.text
