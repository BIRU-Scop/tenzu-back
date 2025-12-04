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
from urllib.parse import parse_qs, urlparse

from allauth.core.exceptions import ImmediateHttpResponse
from allauth.headless.internal.sessionkit import session_store
from allauth.socialaccount.adapter import get_adapter as get_socialaccount_adapter
from allauth.socialaccount.internal import flows
from allauth.socialaccount.internal.flows.signup import (
    clear_pending_signup,
    process_signup,
)
from allauth.socialaccount.models import SocialApp
from allauth.socialaccount.providers.base import AuthProcess, Provider
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponse, HttpResponseRedirect
from ninja import Form, Path, Router

from auth.api.validators import (
    ProviderContinueSignupValidator,
    ProviderRedirectValidator,
)
from auth.decorators import add_allauth_properties
from auth.serializers import AuthConfigSerializer, AuthSocialSignupError
from auth.services import get_auth_config
from base.serializers import BaseDataModel
from commons.exceptions import api as ex
from commons.exceptions.api.errors import (
    ERROR_RESPONSE_400,
    ERROR_RESPONSE_404,
    ERROR_RESPONSE_422,
)
from ninja_jwt.schema import TokenObtainPairOutputSchema

auth_router = Router()


@auth_router.get(
    "/auth/config",
    url_name="auth.config",
    summary="Give information about available auth methods",
    response={
        200: BaseDataModel[AuthConfigSerializer],
    },
    by_alias=True,
    auth=None,
)
@add_allauth_properties
def auth_config(
    request,
) -> AuthConfigSerializer:
    """
    Configuration options that can impact the frontend behaviour.
    The data returned is not user/authentication dependent so data can be fetched only once
    """
    return get_auth_config(request)


@auth_router.post(
    "/auth/provider/{provider_id}/redirect",
    url_name="auth.provider.redirect",
    summary="Redirect to an external provider auth flow",
    response={
        302: None,
        400: ERROR_RESPONSE_400,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
    auth=None,
)
@add_allauth_properties
def redirect_to_provider(
    request,
    provider_id: Path[str],
    form: Form[ProviderRedirectValidator],
) -> HttpResponse:
    """
    Initiates the third-party provider authentication redirect flow.
    As calling this endpoint results in a user facing redirect (302),
     this call is only available in a browser, and must be called in a synchronous (non-XHR) manner.
    """
    provider = get_provider_or_404(request, provider_id)
    return provider.redirect(
        request,
        AuthProcess.LOGIN,
        next_url=form.callback_url,
        headless=True,
        data={
            "accepted_terms": (
                form.accept_terms_of_service and form.accept_privacy_policy
            ),
            **form.model_dump(
                include={
                    "project_invitation_token",
                    "accept_project_invitation",
                    "workspace_invitation_token",
                    "accept_workspace_invitation",
                },
                exclude_unset=True,
            ),
        },
    )


@auth_router.post(
    "/auth/provider/continue_signup",
    url_name="auth.provider.continue_signup",
    summary="Continue pending signup with an external provider auth flow",
    response={
        200: TokenObtainPairOutputSchema | AuthSocialSignupError,
        400: ERROR_RESPONSE_400,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
    auth=None,
)
@add_allauth_properties
def continue_signup_to_provider(
    request,
    form: ProviderContinueSignupValidator,
) -> AuthSocialSignupError | TokenObtainPairOutputSchema:
    """
    Continue an incomplete signup flow,
    Return either the new user auth tokens or the newest error state
    """
    request.session = session_store(form.social_session_key)
    sociallogin = flows.signup.get_pending_signup(request)
    if not sociallogin:
        raise ex.NotFoundError("No pending social login found")
    clear_pending_signup(request)
    data = sociallogin.state.get("data", {})
    sociallogin.state["data"] = {
        **data,
        "accepted_terms": data.get("accepted_terms", False)
        or (form.accept_terms_of_service and form.accept_privacy_policy),
    }
    response: HttpResponseRedirect
    try:
        response = process_signup(request, sociallogin)
    except ImmediateHttpResponse as e:
        response = e.response
    if not isinstance(response, HttpResponseRedirect):
        raise ValueError(response)
    result = {
        key: value[0] for key, value in parse_qs(urlparse(response.url).query).items()
    }
    if "access" in result:
        return TokenObtainPairOutputSchema.model_validate(result)
    return AuthSocialSignupError.model_validate(result)


def get_provider_or_404(request, provider_id: str) -> Provider:
    try:
        provider = get_socialaccount_adapter().get_provider(request, provider_id)
    except (ImproperlyConfigured, SocialApp.DoesNotExist) as e:
        raise ex.NotFoundError(f"Provider {provider_id} does not exist") from e
    return provider
