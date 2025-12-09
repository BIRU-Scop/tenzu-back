# Copyright (C) 2025 BIRU
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

from http import HTTPStatus

from allauth.socialaccount import app_settings
from allauth.socialaccount.adapter import get_adapter
from allauth.socialaccount.providers.gitlab.views import (
    GitLabOAuth2Adapter as AllAuthGitLabOAuth2Adapter,
)
from allauth.socialaccount.providers.gitlab.views import (
    _check_errors as _user_profile_check_errors,
)
from allauth.socialaccount.providers.oauth2.client import OAuth2Error
from allauth.socialaccount.providers.oauth2.views import (
    OAuth2CallbackView,
    OAuth2LoginView,
)


def _emails_check_errors(response):
    """
    Code taken from allauth.socialaccount.providers.gitlab.views._check_errors
    except we change the data format check at the end to expect a list of objects instead of a single object in response
    """
    #  403 error's are presented as user-facing errors
    if response.status_code == HTTPStatus.FORBIDDEN:
        msg = response.content
        raise OAuth2Error("Invalid data from GitLab API: %r" % (msg))

    try:
        data = response.json()
    except ValueError:  # JSONDecodeError on py3
        raise OAuth2Error("Invalid JSON from GitLab API: %r" % (response.text))

    if response.status_code >= HTTPStatus.BAD_REQUEST or "error" in data:
        # For errors, we expect the following format:
        # {"error": "error_name", "error_description": "Oops!"}
        # For example, if the token is not valid, we will get:
        # {"message": "status_code - message"}
        error = data.get("error", "") or response.status_code
        desc = data.get("error_description", "") or data.get("message", "")

        raise OAuth2Error("GitLab error: %s (%s)" % (error, desc))

    # The expected output from the API follows this format:
    # [{"id": 12345, ...}]
    if not isinstance(data, list):
        raise OAuth2Error("Invalid data from GitLab API: %r" % (data))

    return data


class GitLabOAuth2Adapter(AllAuthGitLabOAuth2Adapter):
    @property
    def emails_url(self):
        return self._build_url(f"/api/{self.provider_api_version}/user/emails")

    def complete_login(self, request, app, token, **kwargs):
        response = (
            get_adapter()
            .get_requests_session()
            .get(self.profile_url, params={"access_token": token.token})
        )
        data = _user_profile_check_errors(response)
        if app_settings.QUERY_EMAIL:
            if emails := self.get_emails(token):
                data["emails"] = emails
        return self.get_provider().sociallogin_from_response(request, data)

    def get_emails(self, token) -> list:
        response = (
            get_adapter()
            .get_requests_session()
            .get(self.emails_url, params={"access_token": token.token})
        )
        data = _emails_check_errors(response)
        return data


oauth2_login = OAuth2LoginView.adapter_view(GitLabOAuth2Adapter)
oauth2_callback = OAuth2CallbackView.adapter_view(GitLabOAuth2Adapter)
