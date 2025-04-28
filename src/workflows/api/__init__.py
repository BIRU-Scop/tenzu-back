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

from uuid import UUID

from ninja import Path, Query, Router

from commons.exceptions import api as ex
from commons.exceptions.api.errors import (
    ERROR_RESPONSE_400,
    ERROR_RESPONSE_403,
    ERROR_RESPONSE_404,
    ERROR_RESPONSE_422,
)
from commons.validators import B64UUID
from permissions import check_permissions
from projects.projects.api import get_project_or_404
from workflows import services as workflows_services
from workflows.api.validators import (
    CreateWorkflowStatusValidator,
    CreateWorkflowValidator,
    DeleteWorkflowQuery,
    DeleteWorkflowStatusQuery,
    ReorderWorkflowStatusesValidator,
    UpdateWorkflowStatusValidator,
    UpdateWorkflowValidator,
)
from workflows.models import Workflow, WorkflowStatus
from workflows.permissions import WorkflowPermissionsCheck
from workflows.serializers import (
    ReorderWorkflowStatusesSerializer,
    WorkflowSerializer,
    WorkflowStatusSerializer,
)

workflows_router = Router()

################################################
# create workflow
################################################


@workflows_router.post(
    "/workflows",
    url_name="project.workflow.create",
    summary="Create workflows",
    response={
        200: WorkflowSerializer,
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def create_workflow(
    request,
    form: CreateWorkflowValidator,
) -> WorkflowSerializer:
    """
    Creates a workflow for a project
    """
    project = await get_project_or_404(form.project_id)
    await check_permissions(
        permissions=WorkflowPermissionsCheck.CREATE.value,
        user=request.user,
        obj=project,
    )

    return await workflows_services.create_workflow(
        name=form.name,
        project=project,
    )


################################################
# list workflows
################################################


@workflows_router.get(
    "/projects/{project_id}/workflows",
    url_name="project.workflow.list",
    summary="List workflows",
    response={
        200: list[WorkflowSerializer],
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    tags=["projects", "workflows"],
    by_alias=True,
)
async def list_workflows(
    request,
    project_id: Path[B64UUID],
) -> list[WorkflowSerializer]:
    """
    List the workflows of a project
    """
    project = await get_project_or_404(project_id)
    await check_permissions(
        permissions=WorkflowPermissionsCheck.VIEW.value, user=request.user, obj=project
    )
    return await workflows_services.list_workflows(project_id=project_id)


################################################
# get workflow
################################################


@workflows_router.get(
    "/workflows/{workflow_id}",
    url_name="project.workflow.get",
    summary="Get project workflow",
    response={
        200: WorkflowSerializer,
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def get_workflow(
    request,
    workflow_id: Path[B64UUID],
) -> WorkflowSerializer:
    """
    Get the details of a workflow by id
    """

    workflow = await get_workflow_or_404(workflow_id=workflow_id)
    await check_permissions(
        permissions=WorkflowPermissionsCheck.VIEW.value,
        user=request.user,
        obj=workflow.project,
    )
    return await workflows_services.get_workflow_detail(workflow_id=workflow.id)


@workflows_router.get(
    "/workflows/by_slug/{workflow_slug}/projects/{project_id}",
    url_name="project.workflow.get_by_slug",
    summary="Get project workflow by slug",
    response={
        200: WorkflowSerializer,
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def get_workflow_by_slug(
    request,
    project_id: Path[B64UUID],
    workflow_slug: str,
) -> WorkflowSerializer:
    """
    Get the details of a workflow by slug
    """
    workflow = await get_workflow_by_slug_or_404(
        project_id=project_id, workflow_slug=workflow_slug
    )
    await check_permissions(
        permissions=WorkflowPermissionsCheck.VIEW.value,
        user=request.user,
        obj=workflow.project,
    )
    return await workflows_services.get_workflow_detail(workflow_id=workflow.id)


#########################################################
# update workflow
##########################################################


@workflows_router.patch(
    "/workflows/{workflow_id}",
    url_name="project.workflow.update",
    summary="Update workflow",
    response={
        200: WorkflowSerializer,
        400: ERROR_RESPONSE_400,
        403: ERROR_RESPONSE_403,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def update_workflow(
    request,
    workflow_id: Path[B64UUID],
    form: UpdateWorkflowValidator,
) -> WorkflowSerializer:
    """
    Update workflow
    """
    workflow = await get_workflow_or_404(workflow_id=workflow_id)
    await check_permissions(
        permissions=WorkflowPermissionsCheck.MODIFY.value,
        user=request.user,
        obj=workflow.project,
    )

    values = form.dict(exclude_unset=True)
    return await workflows_services.update_workflow(workflow=workflow, updated_by=request.user, values=values)


################################################
# delete workflow
################################################


@workflows_router.delete(
    "/workflows/{workflow_id}",
    url_name="project.workflow.delete",
    summary="Delete a workflow",
    response={
        204: None,
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def delete_workflow(
    request,
    workflow_id: Path[B64UUID],
    query_params: Query[DeleteWorkflowQuery],
) -> tuple[int, None]:
    """
    Deletes a workflow in the given project, providing the option to move all the statuses and their stories to another
    workflow.

    Query params:

    * **move_to:** the workflow's slug to which move the statuses from the workflow being deleted
        - if not received, the workflow, statuses and its contained stories will be deleted
        - if received, the workflow will be deleted but its statuses and stories won't (they will be appended to the
         last status of the specified workflow).
    """
    workflow = await get_workflow_or_404(workflow_id=workflow_id)
    await check_permissions(
        permissions=WorkflowPermissionsCheck.DELETE.value,
        user=request.user,
        obj=workflow.project,
    )

    await workflows_services.delete_workflow(
        workflow=workflow,
        deleted_by=request.user,
        target_workflow_slug=query_params.move_to,
    )
    return 204, None


################################################
# misc
################################################


async def get_workflow_by_slug_or_404(project_id: UUID, workflow_slug: str) -> Workflow:
    try:
        workflow = await workflows_services.get_workflow_by_slug(
            project_id=project_id, workflow_slug=workflow_slug
        )
    except Workflow.DoesNotExist as e:
        raise ex.NotFoundError(f"Workflow {workflow_slug} does not exist") from e

    return workflow


async def get_workflow_or_404(workflow_id: UUID) -> Workflow:
    try:
        workflow = await workflows_services.get_workflow_by_id(workflow_id=workflow_id)
    except Workflow.DoesNotExist as e:
        raise ex.NotFoundError(f"Workflow {workflow_id} does not exist") from e

    return workflow


################################################
# create workflow status
################################################


@workflows_router.post(
    "/workflows/{workflow_id}/statuses",
    url_name="project.workflowstatus.create",
    summary="Create a workflow status",
    response={
        200: WorkflowStatusSerializer,
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def create_workflow_status(
    request,
    workflow_id: Path[B64UUID],
    form: CreateWorkflowStatusValidator,
) -> WorkflowStatus:
    """
    Creates a workflow status in the given project workflow
    """
    workflow = await get_workflow_or_404(workflow_id=workflow_id)
    await check_permissions(
        permissions=WorkflowPermissionsCheck.MODIFY.value,
        user=request.user,
        obj=workflow.project,
    )

    return await workflows_services.create_workflow_status(
        name=form.name,
        color=form.color,
        workflow=workflow,
    )


################################################
# update - reorder workflow statuses
################################################


@workflows_router.post(
    "/workflows/{workflow_id}/statuses/reorder",
    url_name="project.workflowstatus.reorder",
    summary="Reorder workflow statuses",
    response={
        200: ReorderWorkflowStatusesSerializer,
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def reorder_workflow_statuses(
    request,
    workflow_id: Path[B64UUID],
    form: ReorderWorkflowStatusesValidator,
) -> ReorderWorkflowStatusesSerializer:
    """
    Reorder one or more workflow statuses; it may change workflow and order
    """
    workflow = await get_workflow_or_404(workflow_id=workflow_id)
    await check_permissions(
        permissions=WorkflowPermissionsCheck.MODIFY.value,
        user=request.user,
        obj=workflow.project,
    )
    model_dump = form.model_dump()

    return await workflows_services.reorder_workflow_statuses(
        target_workflow=workflow, **model_dump
    )


################################################
# update workflow status
################################################


@workflows_router.patch(
    "/workflows/{workflow_id}/statuses/{status_id}",
    url_name="project.workflowstatus.update",
    summary="Update workflow status",
    response={
        200: WorkflowStatusSerializer,
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def update_workflow_status(
    request,
    status_id: Path[B64UUID],
    workflow_id: Path[B64UUID],
    form: UpdateWorkflowStatusValidator,
) -> WorkflowStatus:
    """
    Updates a workflow status in the given project workflow
    """
    workflow_status = await get_workflow_status_or_404(
        workflow_id=workflow_id, status_id=status_id
    )
    await check_permissions(
        permissions=WorkflowPermissionsCheck.MODIFY.value,
        user=request.user,
        obj=workflow_status.workflow.project,
    )

    return await workflows_services.update_workflow_status(
        workflow_status=workflow_status,
        values=form.dict(exclude_unset=True),
    )


################################################
# delete workflow status
################################################


@workflows_router.delete(
    "/workflows/{workflow_id}/statuses/{status_id}",
    url_name="project.workflowstatus.delete",
    summary="Delete a workflow status",
    response={
        204: None,
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def delete_workflow_status(
    request,
    status_id: Path[B64UUID],
    workflow_id: Path[B64UUID],
    query_params: Query[DeleteWorkflowStatusQuery],
) -> tuple[int, None]:
    """
    Deletes a workflow status in the given project workflow, providing the option to replace the stories it may contain
    to any other existing workflow status in the same workflow.

    Query params:
    * **move_to:** the workflow status's slug to which move the stories from the status being deleted
        - if not received, the workflow status and its contained stories will be deleted
        - if received, the workflow status will be deleted but its contained stories won't (they will be first moved to
         the specified status).
    """
    workflow_status = await get_workflow_status_or_404(
        workflow_id=workflow_id, status_id=status_id
    )
    await check_permissions(
        permissions=WorkflowPermissionsCheck.MODIFY.value,
        user=request.user,
        obj=workflow_status.workflow.project,
    )

    await workflows_services.delete_workflow_status(
        deleted_by=request.user,
        workflow_status=workflow_status,
        target_status_id=query_params.move_to,  # type: ignore
    )

    return 204, None


################################################
# misc
################################################


async def get_workflow_status_or_404(
    workflow_id: UUID, status_id: UUID
) -> WorkflowStatus:
    try:
        workflow_status = await workflows_services.get_workflow_status(
            workflow_id=workflow_id, status_id=status_id
        )
    except WorkflowStatus.DoesNotExist as e:
        raise ex.NotFoundError("Workflow status does not exist") from e

    return workflow_status
