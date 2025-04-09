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

from tests.utils import factories as f
from tests.utils.bad_params import INVALID_B64ID, NOT_EXISTING_B64ID, NOT_EXISTING_SLUG

pytestmark = pytest.mark.django_db


##########################################################
# Workflow POST /projects/<pj_b64id>/workflows
##########################################################


async def test_create_workflow_200_ok(client, project_template):
    project = await f.create_project(project_template)
    data = {"name": "New workflow"}

    client.login(project.created_by)
    response = await client.post(f"/projects/{project.b64id}/workflows", json=data)
    assert response.status_code == 200, response.data


async def test_create_workflow_403_forbidden_permissions(client, project_template):
    project = await f.create_project(project_template)
    user = await f.create_user()
    data = {"name": "New workflow"}

    client.login(user)
    response = await client.post(f"/projects/{project.b64id}/workflows", json=data)
    assert response.status_code == 403, response.data


async def test_create_workflow_404_not_found_project_b64id(client):
    user = await f.create_user()
    data = {"name": "New workflow"}

    client.login(user)
    response = await client.post(f"/projects/{NOT_EXISTING_B64ID}/workflows", json=data)
    assert response.status_code == 404, response.data


async def test_create_workflow_422_unprocessable_project_b64id(client):
    user = await f.create_user()
    data = {"name": "New workflow"}

    client.login(user)
    response = await client.post(f"/projects/{INVALID_B64ID}/workflows", json=data)
    assert response.status_code == 422, response.data


##########################################################
# Workflow GET /projects/<pj_b64id>/workflows
##########################################################


async def test_get_workflows_200_ok(client, project_template):
    project = await f.create_project(project_template)

    client.login(project.created_by)
    response = await client.get(f"/projects/{project.b64id}/workflows")
    assert response.status_code == 200, response.data


async def test_get_workflows_403_forbidden_permissions(client, project_template):
    project = await f.create_project(project_template)
    user = await f.create_user()

    client.login(user)
    response = await client.get(f"/projects/{project.b64id}/workflows")
    assert response.status_code == 403, response.data


async def test_get_workflows_404_not_found_project_b64id(client):
    user = await f.create_user()
    client.login(user)
    response = await client.get(f"/projects/{NOT_EXISTING_B64ID}/workflows")
    assert response.status_code == 404, response.data


async def test_get_workflows_422_unprocessable_project_b64id(client):
    user = await f.create_user()
    client.login(user)
    response = await client.get(f"/projects/{INVALID_B64ID}/workflows")
    assert response.status_code == 422, response.data


#################################################################
# Workflow GET /projects/<pj_b64id>/workflows/{wf_slug}
#################################################################


async def test_get_workflow_200_ok(client, project_template):
    project = await f.create_project(project_template)
    workflow = await f.create_workflow(project=project)

    client.login(project.created_by)
    response = await client.get(f"/projects/{project.b64id}/workflows/{workflow.slug}")
    assert response.status_code == 200, response.data


async def test_get_workflow_403_forbidden_permissions(client, project_template):
    project = await f.create_project(project_template)
    workflow = await f.create_workflow(project=project)
    user = await f.create_user()

    client.login(user)
    response = await client.get(f"/projects/{project.b64id}/workflows/{workflow.slug}")
    assert response.status_code == 403, response.data


async def test_get_workflow_404_not_found_project_b64id(client, project_template):
    project = await f.create_project(project_template)
    workflow = await f.create_workflow(project=project)

    client.login(project.created_by)
    response = await client.get(
        f"/projects/{NOT_EXISTING_B64ID}/workflows/{workflow.slug}"
    )
    assert response.status_code == 404, response.data


async def test_get_workflow_404_workflow_slug(client, project_template):
    project = await f.create_project(project_template)

    client.login(project.created_by)
    response = await client.get(
        f"/projects/{project.b64id}/workflows/{NOT_EXISTING_SLUG}"
    )
    assert response.status_code == 404, response.data


async def test_get_workflow_422_unprocessable_project_b64id(client, project_template):
    project = await f.create_project(project_template)
    workflow = await f.create_workflow(project=project)

    client.login(project.created_by)
    response = await client.get(f"/projects/{INVALID_B64ID}/workflows/{workflow.slug}")
    assert response.status_code == 422, response.data


#################################################################
# Workflow PATCH /projects/<pj_b64id>/workflows/{wf_slug}
#################################################################


async def test_update_workflow_200_ok(client, project_template):
    project = await f.create_project(project_template)
    workflow = await f.create_workflow(project=project)
    data = {"name": "updated name"}

    client.login(project.created_by)
    response = await client.patch(
        f"/projects/{project.b64id}/workflows/{workflow.slug}", json=data
    )
    assert response.status_code == 200, response.data


async def test_update_workflow_403_forbidden_permissions(client, project_template):
    project = await f.create_project(project_template)
    workflow = await f.create_workflow(project=project)
    user = await f.create_user()
    data = {"name": "updated name"}

    client.login(user)
    response = await client.patch(
        f"/projects/{project.b64id}/workflows/{workflow.slug}", json=data
    )
    assert response.status_code == 403, response.data


async def test_update_workflow_404_not_found_project_b64id(client, project_template):
    project = await f.create_project(project_template)
    workflow = await f.create_workflow(project=project)
    data = {"name": "updated name"}

    client.login(project.created_by)
    response = await client.patch(
        f"/projects/{NOT_EXISTING_B64ID}/workflows/{workflow.slug}", json=data
    )
    assert response.status_code == 404, response.data


async def test_update_workflow_404_workflow_slug(client, project_template):
    project = await f.create_project(project_template)
    data = {"name": "updated name"}

    client.login(project.created_by)
    response = await client.patch(
        f"/projects/{project.b64id}/workflows/{NOT_EXISTING_SLUG}", json=data
    )
    assert response.status_code == 404, response.data


async def test_update_workflow_422_unprocessable_project_b64id(
    client, project_template
):
    project = await f.create_project(project_template)
    workflow = await f.create_workflow(project=project)
    data = {"name": "updated name"}

    client.login(project.created_by)
    response = await client.patch(
        f"/projects/{INVALID_B64ID}/workflows/{workflow.slug}", json=data
    )
    assert response.status_code == 422, response.data


################################################################################
# WorkflowStatus POST /projects/<pj_b64id>/workflows/<wf_slug>/statuses
################################################################################


async def test_create_workflow_status_invalid_workflow(client, project_template):
    project = await f.create_project(project_template)
    await f.create_workflow(project=project)

    data = {"name": "Closed", "color": 5}

    client.login(project.created_by)
    response = await client.post(
        f"/projects/{project.b64id}/workflows/{NOT_EXISTING_SLUG}/statuses", json=data
    )
    assert response.status_code == 404, response.data


async def test_create_workflow_status_being_pj_admin_ok(client, project_template):
    project = await f.create_project(project_template)
    workflow = await f.create_workflow(project=project)

    data = {"name": "Closed", "color": 5}

    client.login(project.created_by)
    response = await client.post(
        f"/projects/{project.b64id}/workflows/{workflow.slug}/statuses", json=data
    )
    assert response.status_code == 200, response.data


async def test_create_workflow_status_forbidden(client, project_template):
    pj_member = await f.create_user()
    project = await f.create_project(project_template)
    pj_role = await f.create_project_role(is_owner=False, project=project)
    await f.create_project_membership(user=pj_member, project=project, role=pj_role)

    workflow = await f.create_workflow(project=project)

    data = {"name": "Closed", "color": 5}

    client.login(pj_member)
    response = await client.post(
        f"/projects/{project.b64id}/workflows/{workflow.slug}/statuses", json=data
    )
    assert response.status_code == 403, response.data


################################################################################
# WorkflowStatus PATCH /projects/<pj_b64id>/workflows/<wf_slug>/statuses/<wf_status_b64id>
################################################################################


async def test_update_status_200_ok(client, project_template):
    project = await f.create_project(project_template)
    workflow = await f.create_workflow(project=project)
    wf_status = await f.create_workflow_status(workflow=workflow)

    data = {"name": "New status name"}

    client.login(project.created_by)
    response = await client.patch(
        f"/projects/{project.b64id}/workflows/{workflow.slug}/statuses/{wf_status.b64id}",
        json=data,
    )
    assert response.status_code == 200, response.data


async def test_update_status_400_bad_request_null_name(client, project_template):
    project = await f.create_project(project_template)
    workflow = await f.create_workflow(project=project)
    wf_status = await f.create_workflow_status(workflow=workflow)

    data = {"name": None}

    client.login(project.created_by)
    response = await client.patch(
        f"/projects/{project.b64id}/workflows/{workflow.slug}/statuses/{wf_status.b64id}",
        json=data,
    )
    assert response.status_code == 400, response.data
    assert response.json()["error"]["msg"] == "Name cannot be null"


async def test_update_status_404_not_found_wf_status_b64id(client, project_template):
    project = await f.create_project(project_template)
    workflow = await f.create_workflow(project=project)

    data = {"name": "New status name"}

    client.login(project.created_by)
    response = await client.patch(
        f"/projects/{project.b64id}/workflows/{workflow.slug}/statuses/{NOT_EXISTING_B64ID}",
        json=data,
    )
    assert response.status_code == 404, response.data


async def test_update_status_422_unprocessable_wf_status_b64id(
    client, project_template
):
    project = await f.create_project(project_template)
    workflow = await f.create_workflow(project=project)

    data = {"name": "New status name"}

    client.login(project.created_by)
    response = await client.patch(
        f"/projects/{project.b64id}/workflows/{workflow.slug}/statuses/{INVALID_B64ID}",
        json=data,
    )
    assert response.status_code == 422, response.data


################################################################################
# Workflow DELETE /projects/<pj_b64id>/workflows/<ws_slug>
################################################################################


async def test_delete_workflow_204_ok(client, project_template):
    project = await f.create_project(project_template)
    deleted_workflow = await f.create_workflow(project=project)
    f.build_workflow_status(workflow=deleted_workflow, order=1)
    f.build_workflow_status(workflow=deleted_workflow, order=2)
    target_workflow = await f.create_workflow(project=project)
    f.build_workflow_status(workflow=target_workflow, order=1)
    f.build_workflow_status(workflow=target_workflow, order=2)

    client.login(project.created_by)
    response = await client.delete(
        f"/projects/{project.b64id}/workflows/{deleted_workflow.slug}?moveTo={target_workflow.slug}"
    )
    assert response.status_code == 204, response.data


async def test_delete_workflow_403_not_project_admin(client, project_template):
    project = await f.create_project(project_template)
    workflow = await f.create_workflow(project=project)
    another_user = await f.create_user()

    client.login(another_user)
    response = await client.delete(
        f"/projects/{project.b64id}/workflows/{workflow.slug}"
    )
    assert response.status_code == 403, response.data


async def test_delete_workflow_404_not_found_project_b64id(client, project_template):
    project = await f.create_project(project_template)
    workflow = await f.create_workflow(project=project)
    client.login(project.created_by)
    response = await client.delete(
        f"/projects/{NOT_EXISTING_B64ID}/workflows/{workflow.slug}"
    )
    assert response.status_code == 404, response.data


async def test_delete_workflow_422_empty_move_to_slug(client, project_template):
    project = await f.create_project(project_template)
    client.login(project.created_by)
    empty_string = ""
    response = await client.delete(
        f"/projects/{project.b64id}/workflows/slug?moveTo={empty_string}"
    )
    assert response.status_code == 422, response.data


async def test_delete_workflow_422_long_move_to_slug(client, project_template):
    project = await f.create_project(project_template)
    client.login(project.created_by)
    long_string = "slug_" * 100
    response = await client.delete(
        f"/projects/{project.b64id}/workflows/slug?moveTo={long_string}"
    )
    assert response.status_code == 422, response.data


##########################################################
# Workflow Status POST /projects/<slug>/workflows/<slug>/statuses/reorder
##########################################################


async def test_reorder_statuses_200_ok_with_reorder_ok(client, project_template):
    pj = await f.create_project(project_template)
    workflow = await sync_to_async(pj.workflows.first)()
    wf_status = await sync_to_async(workflow.statuses.first)()
    reorder_status = await sync_to_async(workflow.statuses.last)()

    data = {
        "statuses": [wf_status.b64id],
        "reorder": {"place": "before", "status": reorder_status.b64id},
    }
    client.login(pj.created_by)
    response = await client.post(
        f"/projects/{pj.b64id}/workflows/main/statuses/reorder", json=data
    )

    assert response.status_code == 200, response.data
    res = response.json()
    assert "reorder" in res
    assert "statuses" in res
    assert res["statuses"] == [wf_status.b64id]


async def test_reorder_statuses_404_not_found_pj_b64id(client, project_template):
    pj = await f.create_project(project_template)
    workflow = await sync_to_async(pj.workflows.first)()
    wf_status = await sync_to_async(workflow.statuses.first)()
    reorder_status = await sync_to_async(workflow.statuses.last)()

    data = {
        "statuses": [wf_status.b64id],
        "reorder": {"place": "before", "status": reorder_status.b64id},
    }
    client.login(pj.created_by)
    response = await client.post(
        f"/projects/{NOT_EXISTING_B64ID}/workflows/main/statuses/reorder", json=data
    )

    assert response.status_code == 404, response.data


async def test_reorder_statuses_404_not_found_workflow_slug(client, project_template):
    pj = await f.create_project(project_template)
    workflow = await sync_to_async(pj.workflows.first)()
    wf_status = await sync_to_async(workflow.statuses.first)()
    reorder_status = await sync_to_async(workflow.statuses.last)()

    data = {
        "statuses": [wf_status.b64id],
        "reorder": {"place": "before", "status": reorder_status.b64id},
    }
    client.login(pj.created_by)
    response = await client.post(
        f"/projects/{pj.b64id}/workflows/{NOT_EXISTING_SLUG}/statuses/reorder",
        json=data,
    )

    assert response.status_code == 404, response.data


async def test_reorder_statuses_422_unprocessable_pj_b64id(client, project_template):
    pj = await f.create_project(project_template)
    workflow = await sync_to_async(pj.workflows.first)()
    wf_status = await sync_to_async(workflow.statuses.first)()
    reorder_status = await sync_to_async(workflow.statuses.last)()

    data = {
        "statuses": [wf_status.b64id],
        "reorder": {"place": "before", "status": reorder_status.b64id},
    }
    client.login(pj.created_by)
    response = await client.post(
        f"/projects/{INVALID_B64ID}/workflows/main/statuses/reorder", json=data
    )

    assert response.status_code == 422, response.data


################################################################################
# WorkflowStatus DELETE /projects/<pj_b64id>/workflows/<wf_slug>/statuses/<ws_slug>
################################################################################


async def test_delete_workflow_status_204_ok(client, project_template):
    project = await f.create_project(project_template)
    wf = await f.create_workflow(project=project)
    wf_status1 = await f.create_workflow_status(workflow=wf)
    wf_status2 = await f.create_workflow_status(workflow=wf)
    await f.create_story(status=wf_status1, workflow=wf)

    client.login(project.created_by)
    response = await client.delete(
        f"/projects/{project.b64id}/workflows/{wf.slug}/statuses/{wf_status1.b64id}?moveTo={wf_status2.b64id}"
    )
    assert response.status_code == 204, response.data


async def test_delete_workflow_status_400_bad_request_move_to_b64id(
    client, project_template
):
    project = await f.create_project(project_template)
    wf = await f.create_workflow(project=project)
    wf_status1 = await f.create_workflow_status(workflow=wf)
    await f.create_story(status=wf_status1, workflow=wf)
    client.login(project.created_by)
    response = await client.delete(
        f"/projects/{project.b64id}/workflows/{wf.slug}/statuses/{wf_status1.b64id}?moveTo={NOT_EXISTING_B64ID}"
    )
    assert response.status_code == 400, response.data


async def test_delete_workflow_status_403_not_project_admin(client, project_template):
    project = await f.create_project(project_template)
    wf = await f.create_workflow(project=project)
    wf_status = await f.create_workflow_status(workflow=wf)
    another_user = await f.create_user()

    client.login(another_user)
    response = await client.delete(
        f"/projects/{project.b64id}/workflows/{wf.slug}/statuses/{wf_status.b64id}"
    )
    assert response.status_code == 403, response.data


async def test_delete_workflow_status_404_not_found_project_b64id(
    client, project_template
):
    project = await f.create_project(project_template)
    wf = await f.create_workflow(project=project)
    wf_status1 = await f.create_workflow_status(workflow=wf)
    client.login(project.created_by)
    response = await client.delete(
        f"/projects/{NOT_EXISTING_B64ID}/workflows/{wf.slug}/statuses/{wf_status1.b64id}"
    )
    assert response.status_code == 404, response.data


async def test_delete_workflow_status_404_not_found_workflow_slug(
    client, project_template
):
    project = await f.create_project(project_template)
    wf = await f.create_workflow(project=project)
    wf_status1 = await f.create_workflow_status(workflow=wf)
    client.login(project.created_by)
    response = await client.delete(
        f"/projects/{project.b64id}/workflows/{NOT_EXISTING_SLUG}/statuses/{wf_status1.b64id}"
    )
    assert response.status_code == 404, response.data


async def test_delete_workflow_status_404_wf_status_b64id(client, project_template):
    project = await f.create_project(project_template)
    wf = await f.create_workflow(project=project)
    client.login(project.created_by)
    response = await client.delete(
        f"/projects/{project.b64id}/workflows/{wf.slug}/statuses/{NOT_EXISTING_B64ID}"
    )
    assert response.status_code == 404, response.data


async def test_delete_workflow_status_422_unprocessable_project_b64id(
    client, project_template
):
    project = await f.create_project(project_template)
    wf = await f.create_workflow(project=project)
    wf_status1 = await f.create_workflow_status(workflow=wf)
    client.login(project.created_by)
    response = await client.delete(
        f"/projects/{INVALID_B64ID}/workflows/{wf.slug}/statuses/{wf_status1.b64id}"
    )
    assert response.status_code == 422, response.data


async def test_delete_workflow_status_422_unprocessable_wf_status_b64id(
    client, project_template
):
    project = await f.create_project(project_template)
    wf = await f.create_workflow(project=project)
    client.login(project.created_by)
    response = await client.delete(
        f"/projects/{project.b64id}/workflows/{wf.slug}/statuses/{INVALID_B64ID}"
    )
    assert response.status_code == 422, response.data


async def test_delete_wf_status_422_unprocessable_move_to_b64id(
    client, project_template
):
    project = await f.create_project(project_template)
    wf = await f.create_workflow(project=project)
    wf_status1 = await f.create_workflow_status(workflow=wf)
    await f.create_story(status=wf_status1, workflow=wf)
    client.login(project.created_by)
    response = await client.delete(
        f"/projects/{project.b64id}/workflows/{wf.slug}/statuses/{wf_status1.b64id}?moveTo={INVALID_B64ID}"
    )
    assert response.status_code == 422, response.data
