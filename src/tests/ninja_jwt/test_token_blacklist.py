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

# Copyright 2021 Ezeudoh Tochukwu
# https://github.com/eadwinCode/django-ninja-jwt
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.db.models import BigAutoField

from ninja_jwt.exceptions import TokenError, ValidationError
from ninja_jwt.schema import TokenVerifyInputSchema
from ninja_jwt.settings import api_settings
from ninja_jwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from ninja_jwt.tokens import AccessToken, RefreshToken, SlidingToken
from ninja_jwt.utils import aware_utcnow, datetime_from_epoch

from ..utils.factories import sync_create_user as create_user
from .utils import MigrationTestCase


@pytest.mark.django_db
class TestTokenBlacklist:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.user = create_user(
            username="test_user",
            password="test_password",
        )

    def test_sliding_tokens_are_added_to_outstanding_list(self):
        token = SlidingToken.for_user(self.user)

        qs = OutstandingToken.objects.all()
        outstanding_token = qs.first()

        assert qs.count() == 1
        assert outstanding_token.user == self.user
        assert outstanding_token.jti == token["jti"]
        assert outstanding_token.token == str(token)
        assert outstanding_token.created_at == token.current_time
        assert outstanding_token.expires_at == datetime_from_epoch(token["exp"])

    def test_refresh_tokens_are_added_to_outstanding_list(self):
        token = RefreshToken.for_user(self.user)

        qs = OutstandingToken.objects.all()
        outstanding_token = qs.first()

        assert qs.count() == 1
        assert outstanding_token.user == self.user
        assert outstanding_token.jti == token["jti"]
        assert outstanding_token.token == str(token)
        assert outstanding_token.created_at == token.current_time
        assert outstanding_token.expires_at == datetime_from_epoch(token["exp"])

    def test_access_tokens_are_not_added_to_outstanding_list(self):
        AccessToken.for_user(self.user)

        qs = OutstandingToken.objects.all()

        assert not qs.exists()

    def test_token_will_not_validate_if_blacklisted(self):
        token = RefreshToken.for_user(self.user)
        outstanding_token = OutstandingToken.objects.first()

        # Should raise no exception
        RefreshToken(str(token))

        # Add token to blacklist
        BlacklistedToken.objects.create(token=outstanding_token)

        with pytest.raises(TokenError) as e:
            # Should raise exception
            RefreshToken(str(token))
            assert "blacklisted" in e.exception.args[0]

        # Delete the User and try again
        self.user.delete()

        with pytest.raises(TokenError) as e:
            # Should raise exception
            RefreshToken(str(token))
            assert "blacklisted" in e.exception.args[0]

    def test_tokens_can_be_manually_blacklisted(self):
        token = RefreshToken.for_user(self.user)

        # Should raise no exception
        RefreshToken(str(token))

        assert OutstandingToken.objects.count() == 1

        # Add token to blacklist
        blacklisted_token, created = token.blacklist()

        # Should not add token to outstanding list if already present
        assert OutstandingToken.objects.count() == 1

        # Should return blacklist record and boolean to indicate creation
        assert blacklisted_token.token.jti == token["jti"]
        assert created

        with pytest.raises(TokenError) as e:
            # Should raise exception
            RefreshToken(str(token))
            assert "blacklisted" in e.exception.args[0]

        # If blacklisted token already exists, indicate no creation through
        # boolean
        blacklisted_token, created = token.blacklist()
        assert blacklisted_token.token.jti == token["jti"]
        assert not created

        # Should add token to outstanding list if not already present
        new_token = RefreshToken()
        blacklisted_token, created = new_token.blacklist()
        assert blacklisted_token.token.jti == new_token["jti"]
        assert created

        assert OutstandingToken.objects.count() == 2


@pytest.mark.django_db
class TestTokenBlacklistFlushExpiredTokens:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.user = create_user(
            username="test_user",
            password="test_password",
        )

    def test_it_should_delete_any_expired_tokens(self):
        # Make some tokens that won't expire soon
        not_expired_1 = RefreshToken.for_user(self.user)
        not_expired_2 = RefreshToken.for_user(self.user)
        not_expired_3 = RefreshToken()

        # Blacklist fresh tokens
        not_expired_2.blacklist()
        not_expired_3.blacklist()

        # Make tokens with fake exp time that will expire soon
        fake_now = aware_utcnow() - api_settings.REFRESH_TOKEN_LIFETIME

        with patch("ninja_jwt.tokens.aware_utcnow") as fake_aware_utcnow:
            fake_aware_utcnow.return_value = fake_now
            expired_1 = RefreshToken.for_user(self.user)
            expired_2 = RefreshToken()

        # Blacklist expired tokens
        expired_1.blacklist()
        expired_2.blacklist()

        # Make another token that won't expire soon
        not_expired_4 = RefreshToken.for_user(self.user)

        # Should be certain number of outstanding tokens and blacklisted
        # tokens
        assert OutstandingToken.objects.count() == 6
        assert BlacklistedToken.objects.count() == 4

        call_command("flushexpiredtokens")

        # Expired outstanding *and* blacklisted tokens should be gone
        assert OutstandingToken.objects.count() == 4
        assert BlacklistedToken.objects.count() == 2

        assert [i.jti for i in OutstandingToken.objects.order_by("id")] == [
            not_expired_1["jti"],
            not_expired_2["jti"],
            not_expired_3["jti"],
            not_expired_4["jti"],
        ]

        assert [i.token.jti for i in BlacklistedToken.objects.order_by("id")] == [
            not_expired_2["jti"],
            not_expired_3["jti"],
        ]

    def test_token_blacklist_will_not_be_removed_on_User_delete(self):
        token = RefreshToken.for_user(self.user)
        outstanding_token = OutstandingToken.objects.first()

        # Should raise no exception
        RefreshToken(str(token))

        # Add token to blacklist
        BlacklistedToken.objects.create(token=outstanding_token)

        with pytest.raises(TokenError) as e:
            # Should raise exception
            RefreshToken(str(token))
            assert "blacklisted" in e.exception.args[0]

        # Delete the User and try again
        self.user.delete()

        with pytest.raises(TokenError) as e:
            # Should raise exception
            RefreshToken(str(token))
            assert "blacklisted" in e.exception.args[0]


@pytest.mark.django_db
class TestTokenVerifyInputSchemaShouldHonourBlacklist(MigrationTestCase):
    migrate_from = ("token_blacklist", "0002_outstandingtoken_jti_hex")
    migrate_to = ("token_blacklist", "0003_auto_20171017_2007")

    @pytest.fixture(autouse=True)
    def setUp(self):
        self.user = create_user(
            username="test_user",
            password="test_password",
        )
        super().setUp()

    def test_token_verify_serializer_should_honour_blacklist_if_blacklisting_enabled(
        self, monkeypatch
    ):
        with monkeypatch.context() as m:
            m.setattr(api_settings, "BLACKLIST_AFTER_ROTATION", True)
            refresh_token = RefreshToken.for_user(self.user)
            refresh_token.blacklist()

            with pytest.raises(ValidationError):
                TokenVerifyInputSchema(token=str(refresh_token))

    def test_token_verify_serializer_should_not_honour_blacklist_if_blacklisting_not_enabled(
        self, monkeypatch
    ):
        with monkeypatch.context() as m:
            m.setattr(api_settings, "BLACKLIST_AFTER_ROTATION", False)
            refresh_token = RefreshToken.for_user(self.user)
            refresh_token.blacklist()

            serializer = TokenVerifyInputSchema(token=str(refresh_token))
            assert serializer.token == str(refresh_token)


@pytest.mark.django_db
class TestBigAutoFieldIDMigration(MigrationTestCase):
    migrate_from = ("token_blacklist", "0007_auto_20171017_2214")
    migrate_to = ("token_blacklist", "0008_migrate_to_bigautofield")

    @pytest.fixture(autouse=True)
    def setUp(self):
        self.user = create_user(
            username="test_user",
            password="test_password",
        )
        super().setUp()

    def test_outstandingtoken_id_field_is_biagauto_field(self):
        OutstandingToken = self.apps.get_model("token_blacklist", "OutstandingToken")
        assert isinstance(OutstandingToken._meta.get_field("id"), BigAutoField)

    def test_blacklistedtoken_id_field_is_biagauto_field(self):
        BlacklistedToken = self.apps.get_model("token_blacklist", "BlacklistedToken")
        assert isinstance(BlacklistedToken._meta.get_field("id"), BigAutoField)
