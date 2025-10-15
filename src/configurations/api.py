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
from collections import defaultdict
from importlib import import_module

from django.conf import settings
from ninja import NinjaAPI, Router, Swagger
from ninja.params import models as params_models

from base.services.exceptions import TenzuServiceException
from base.utils.strings import to_kebab
from commons.exceptions.api import codes
from commons.parsers import ORJSONParser
from commons.renderers import ORJSONRenderer
from ninja_jwt.api import auth_router
from ninja_jwt.authentication import AsyncJWTAuth
from ninja_jwt.ninja_extra.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from notifications.api import notifications_router
from projects.invitations.api import invitations_router as projects_invitations_router
from projects.memberships.api import (
    project_membership_router as projects_memberships_router,
)
from projects.projects.api import projects_router
from stories.assignments.api import assignments_router as stories_assignments_router
from stories.attachments.api import attachments_router as stories_attachments_router
from stories.comments.api import comments_router as stories_comments_router
from stories.stories.api import stories_router as stories_router
from system.api import system_router
from users.api import users_router
from workflows.api import workflows_router
from workspaces.invitations.api import workspace_invit_router
from workspaces.memberships.api import workspace_membership_router
from workspaces.workspaces.api import workspace_router

api = NinjaAPI(
    docs=Swagger(settings={"filter": True, "showCommonExtensions": True}),
    parser=ORJSONParser(),
    renderer=ORJSONRenderer(),
    title="Tenzu API",
    version=settings.API_VERSION,
    auth=AsyncJWTAuth(),
)


@api.exception_handler(TenzuServiceException)
def tenzu_exception(request, exc):
    return api.create_response(
        request,
        {
            "error": {
                "code": codes.EX_BAD_REQUEST.code,
                "detail": to_kebab(exc.__class__.__name__),
                "msg": str(exc),
            }
        },
        status=HTTP_400_BAD_REQUEST,
    )


health_router = Router()


@health_router.get(
    "/healthcheck",
    summary="Healthcheck",
    response={
        200: None,
    },
    auth=None,
)
def healthcheck(request):
    return HTTP_200_OK


api.add_router("", tags=["projects"], router=projects_router)
api.add_router("", tags=["projects", "memberships"], router=projects_memberships_router)
api.add_router("", tags=["projects", "invitations"], router=projects_invitations_router)
api.add_router("", tags=["system"], router=system_router)
api.add_router("", tags=["stories"], router=stories_router)
api.add_router("", tags=["stories", "assignments"], router=stories_assignments_router)
api.add_router("", tags=["stories", "comments"], router=stories_comments_router)
api.add_router("", tags=["stories", "attachments"], router=stories_attachments_router)
api.add_router("", tags=["users"], router=users_router)
api.add_router("", tags=["notifications"], router=notifications_router)
api.add_router("", tags=["workspaces"], router=workspace_router)
api.add_router("", tags=["workspaces", "invitations"], router=workspace_invit_router)
api.add_router(
    "", tags=["workspaces", "memberships"], router=workspace_membership_router
)
api.add_router("", tags=["workflows"], router=workflows_router)
api.add_router("", tags=["auth"], router=auth_router)
# api.add_router("", tags=["auth"], router=github_integration_router)
# api.add_router("", tags=["auth"], router=gitlab_integration_router)
# api.add_router("", tags=["auth"], router=google_integration_router)
api.add_router("", tags=["system"], router=health_router)

for extra_dep in settings.EXTRA_DEPS:
    if extra_dep.api is not None:
        extra_api = import_module(extra_dep.api)
        api.add_router("", tags=getattr(extra_api, "tags", []), router=extra_api.router)


def patch_resolve():
    """
    temporary hack while waiting for resolution of issue with ninja + pydantic 2.12 compatibility,
    see https://github.com/vitalik/django-ninja/issues/1557#issuecomment-3393588046
    """
    _orig_resolve = params_models.ParamModel.resolve

    def _deep_unwrap_defaultdict(value):
        if isinstance(value, defaultdict) or isinstance(value, dict):
            return {k: _deep_unwrap_defaultdict(v) for k, v in value.items()}
        if isinstance(value, list):
            return [_deep_unwrap_defaultdict(v) for v in value]
        return value

    @classmethod
    def _patched_resolve(cls, request, api, path_params):
        data = cls.get_request_data(request, api, path_params)
        if data is None:
            return cls()

        data = cls._map_data_paths(data)
        data = _deep_unwrap_defaultdict(data)  # <-- this is the hack
        return cls.model_validate(data, context={"request": request})

    params_models.ParamModel.resolve = _patched_resolve


patch_resolve()
