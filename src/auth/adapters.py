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
from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.utils import user_field
from allauth.core.exceptions import ImmediateHttpResponse
from allauth.core.internal import httpkit
from allauth.headless.adapter import DefaultHeadlessAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.internal.flows.signup import redirect_to_signup
from asgiref.sync import async_to_sync
from django.conf import settings
from django.http import HttpResponseRedirect

from auth.services import create_auth_credentials
from ninja_jwt.settings import api_settings
from users import services as users_services
from users.models import User


class AccountAdapter(DefaultAccountAdapter):
    def save_user(self, request, user, form, commit=True):
        raise NotImplementedError

    def send_account_already_exists_mail(self, email):
        pass

    def send_mail(self, template_prefix, email, context):
        raise NotImplementedError

    def pre_login(
        self,
        request,
        user,
        *,
        email_verification,
        signal_kwargs,
        email,
        signup,
        redirect_url,
    ):
        """
        This function is what make social auth works with JWT
        """
        sociallogin = signal_kwargs["sociallogin"]
        if not api_settings.USER_AUTHENTICATION_RULE(user):
            social_adapter = SocialAccountAdapter(request)
            data = sociallogin.state.get("data", {})
            if not signup:
                social_adapter.create_or_update_user(sociallogin, user)
            if social_adapter.is_verified(sociallogin):
                auth_schema = async_to_sync(users_services.verify_user)(
                    user, **data
                ).auth
            else:
                redirect_url = httpkit.add_query_params(
                    redirect_url,
                    {
                        "error": "unverified",
                        "error_process": sociallogin.state["process"],
                        "email": user.email,
                    },
                )
                raise ImmediateHttpResponse(HttpResponseRedirect(redirect_url))
        else:
            auth_schema = async_to_sync(create_auth_credentials)(user)
        sociallogin.state["next"] = httpkit.add_query_params(
            redirect_url,
            auth_schema.dict(),
        )
        return HttpResponseRedirect(sociallogin.state["next"])


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def is_auto_signup_allowed(self, request, sociallogin):
        if settings.REQUIRED_TERMS and not sociallogin.state.get("data", {}).get(
            "accepted_terms"
        ):
            if not request.session.session_key:
                request.session.create()
            redirect_to_signup(request, sociallogin)  # fill session data
            redirect_url = httpkit.add_query_params(
                sociallogin.state["next"],
                {
                    "error": "missing_terms_acceptance",
                    "error_process": sociallogin.state["process"],
                    "socialSessionKey": request.session.session_key,
                },
            )
            raise ImmediateHttpResponse(HttpResponseRedirect(redirect_url))
        return super().is_auto_signup_allowed(request, sociallogin)

    def is_verified(self, sociallogin) -> bool:
        return sociallogin.email_addresses and sociallogin.email_addresses[0].verified

    def create_or_update_user(self, sociallogin, user) -> User:
        return async_to_sync(users_services.create_user)(
            email=user.email,
            full_name=user.full_name,
            password=None,
            skip_verification_mail=self.is_verified(sociallogin),
            **sociallogin.state.get("data", {}),
        )

    def save_user(self, request, sociallogin, form=None):
        user = self.create_or_update_user(sociallogin, sociallogin.user)
        sociallogin.user = user
        sociallogin.save(request)
        return user

    def populate_user(self, request, sociallogin, data):
        first_name = data.get("first_name")
        last_name = data.get("last_name")
        name = data.get("name")
        user = super().populate_user(request, sociallogin, data)
        user_field(user, "full_name", name or f"{first_name} {last_name}")
        return user


class HeadlessAdapter(DefaultHeadlessAdapter):
    pass
