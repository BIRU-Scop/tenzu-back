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

from unittest.mock import PropertyMock, patch

from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount, SocialLogin
from babel import Locale

from auth.adapters import SocialAccountAdapter


class TestSocialAccountAdapter:
    def test_is_verified(self):
        adapter = SocialAccountAdapter()
        sociallogin = SocialLogin(
            email_addresses=[
                EmailAddress(email="test0", verified=False),
                EmailAddress(email="test1", verified=True),
                EmailAddress(email="test2", verified=False),
            ]
        )
        assert not adapter.is_verified(sociallogin, "test0")
        assert adapter.is_verified(sociallogin, "test1")
        assert not adapter.is_verified(sociallogin, "test2")
        assert not adapter.is_verified(sociallogin, "unknown")

    def test_get_language(self):
        adapter = SocialAccountAdapter()
        sociallogin = SocialLogin(account=SocialAccount(extra_data={}))
        assert adapter.get_language(sociallogin) is None
        sociallogin = SocialLogin(
            account=SocialAccount(extra_data={"preferred_language": {"bad_format"}})
        )
        assert adapter.get_language(sociallogin) is None
        sociallogin = SocialLogin(
            account=SocialAccount(extra_data={"preferred_language": "en"})
        )
        assert adapter.get_language(sociallogin) == "en-US"
        sociallogin = SocialLogin(account=SocialAccount(extra_data={"locale": "fr"}))
        assert adapter.get_language(sociallogin) == "fr-FR"
        sociallogin = SocialLogin(account=SocialAccount(extra_data={"locale": "fr-FR"}))
        assert adapter.get_language(sociallogin) == "fr-FR"
        with patch("base.i18n.I18N.locales", new_callable=PropertyMock) as locales_mock:
            locales_mock.return_value = [
                Locale.parse(cod, sep="-") for cod in ["en-US", "en-GB"]
            ]
            sociallogin = SocialLogin(
                account=SocialAccount(extra_data={"preferred_language": "en-GB"})
            )
            assert adapter.get_language(sociallogin) == "en-GB"
            sociallogin = SocialLogin(
                account=SocialAccount(extra_data={"preferred_language": "en-CA"})
            )
            assert adapter.get_language(sociallogin) == "en-US"

    def test_populate_user(self):
        adapter = SocialAccountAdapter()
        user = adapter.new_user(None, SocialLogin())
        sociallogin = SocialLogin(user=user, account=SocialAccount(extra_data={}))
        user = adapter.populate_user(None, sociallogin, {})
        assert user.full_name == " "
        assert user.lang is None
        user = adapter.populate_user(
            None, sociallogin, {"first_name": "foo", "last_name": "bar"}
        )
        assert user.full_name == "foo bar"
        sociallogin = SocialLogin(
            user=user, account=SocialAccount(extra_data={"name": "toto"})
        )
        user = adapter.populate_user(None, sociallogin, {})
        assert user.full_name == "toto"
        user = adapter.populate_user(None, sociallogin, {"name": "tata"})
        assert user.full_name == "tata"
