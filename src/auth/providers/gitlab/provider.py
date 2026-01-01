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

from allauth.account.models import EmailAddress
from allauth.socialaccount.providers.gitlab.provider import (
    GitLabProvider as AllAuthGitLabProvider,
)

from auth.providers.gitlab.views import GitLabOAuth2Adapter


class GitLabProvider(AllAuthGitLabProvider):
    oauth2_adapter_class = GitLabOAuth2Adapter

    def extract_extra_data(self, data):
        if "emails" in data:
            data = dict(data)
            data.pop("emails")
        return data

    def extract_email_addresses(self, data):
        ret = []
        primary_email = data.get("email", "")
        for email in data.get("emails", []):
            ret.append(
                EmailAddress(
                    email=email["email"],
                    primary=email["email"] == primary_email,
                    verified=email["confirmed_at"] is not None,
                )
            )
        return ret


provider_classes = [GitLabProvider]
