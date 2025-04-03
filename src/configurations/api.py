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
from django.conf import settings
from ninja import NinjaAPI, Router

from base.services.exceptions import TenzuServiceException
from base.utils.strings import to_kebab
from commons.exceptions.api import codes
from commons.parsers import ORJSONParser
from commons.renderers import ORJSONRenderer
from integrations.github.auth.api import github_integration_router
from integrations.gitlab.auth.api import gitlab_integration_router
from integrations.google.auth.api import google_integration_router
from ninja_jwt.api import auth_router
from ninja_jwt.authentication import AsyncJWTAuth
from ninja_jwt.ninja_extra.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from notifications.api import notifications_router
from projects.invitations.api import invitations_router as projects_invitations_router
from projects.memberships.api import membership_router as projects_memberships_router
from projects.projects.api import projects_router
from stories.assignments.api import assignments_router as stories_assignments_router
from stories.attachments.api import attachments_router as stories_attachments_router
from stories.comments.api import comments_router as stories_comments_router
from stories.mediafiles.api import mediafiles_router as stories_mediafiles_router
from stories.stories.api import stories_router as stories_router
from system.api import system_router
from users.api import users_router
from workflows.api import workflows_router
from workspaces.invitations.api import workspace_invit_router
from workspaces.memberships.api import workspace_membership_router
from workspaces.workspaces.api import workspace_router

api = NinjaAPI(
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


api.add_router("", tags=["Projects"], router=projects_router)
api.add_router("", tags=["Projects", "Memberships"], router=projects_memberships_router)
api.add_router("", tags=["Projects", "Invitations"], router=projects_invitations_router)
api.add_router("", system_router)
api.add_router("", tags=["Stories"], router=stories_router)
api.add_router("", tags=["Stories", "Assignments"], router=stories_assignments_router)
api.add_router("", tags=["Stories", "Comments"], router=stories_comments_router)
api.add_router("", tags=["Stories", "Mediafiles"], router=stories_mediafiles_router)
api.add_router("", tags=["Stories", "Attachments"], router=stories_attachments_router)
api.add_router("", tags=["Users"], router=users_router)
api.add_router("", tags=["Notifications"], router=notifications_router)
api.add_router("", tags=["Workspaces"], router=workspace_router)
api.add_router("", tags=["Workspaces", "Invitations"], router=workspace_invit_router)
api.add_router(
    "", tags=["Workspaces", "Memberships"], router=workspace_membership_router
)
api.add_router("", tags=["Workflows"], router=workflows_router)
api.add_router("", tags=["Auth"], router=auth_router)
api.add_router("", tags=["Auth", "Github"], router=github_integration_router)
api.add_router("", tags=["Auth", "Gitlab"], router=gitlab_integration_router)
api.add_router("", tags=["Auth", "Google"], router=google_integration_router)
api.add_router("", tags=["Healthcheck"], router=health_router)
