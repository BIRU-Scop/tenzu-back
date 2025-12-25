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
from unittest.mock import patch

import pytest
from django.conf import settings
from django.test import override_settings

from tests.auth.utils import provider_auth
from tests.utils import factories as f
from users.services import verify_user

pytestmark = pytest.mark.django_db


##########################################################
# GET /auth/config
##########################################################


def test_auth_config(sync_client):
    response = sync_client.get("/auth/config")
    assert response.status_code == 200, response.data["data"]
    res = response.data["data"]
    assert [provider["id"] for provider in res["socialaccount"]["providers"]] == [
        "dummy"
    ]


def test_redirect_to_provider_provider_not_found(ssr_client):
    data = {"callbackUrl": "/test"}
    response = ssr_client.post(
        f"/api/{settings.API_VERSION}/auth/provider/unknown/redirect", data=data
    )
    assert response.status_code == 404, response.data


def test_redirect_to_provider_invalid_data(ssr_client):
    data = {"callbackUrl": "invalid"}
    response = ssr_client.post(
        f"/api/{settings.API_VERSION}/auth/provider/dummy/redirect", data=data
    )
    assert response.status_code == 422, response.data


def test_redirect_to_provider_ok_signup(ssr_client):
    post_data = {
        "callbackUrl": "/test?customValue=keep_it&next=/accept-project-invitation/token",
        "acceptTermsOfService": True,
        "acceptPrivacyPolicy": True,
    }
    user_data = {
        "id": 0,
        "email": "test@email.com",
        "email_verified": True,
        "username": "",
        "first_name": "",
        "last_name": "",
        "phone": "",
        "phone_verified": False,
    }
    with patch(
        "auth.adapters.users_services.verify_user", autospec=True, wraps=verify_user
    ) as fake_verify_user:
        callback_url, query = provider_auth(ssr_client, post_data, user_data)
        assert "error" not in query
        assert "access" in query
        assert "refresh" in query
        assert "username" in query
        assert query["next"] == ["/accept-project-invitation/token"]
        assert query["customValue"] == ["keep_it"]
        fake_verify_user.assert_awaited_once()


def test_redirect_to_provider_ok_login(ssr_client):
    user = f.sync_create_user()
    post_data = {
        "callbackUrl": "/test?customValue=keep_it&next=/accept-project-invitation/token",
        "acceptTermsOfService": True,
        "acceptPrivacyPolicy": True,
    }
    user_data = {
        "id": 0,
        "email": user.email,
        "email_verified": True,
        "username": "",
        "first_name": "",
        "last_name": "",
        "phone": "",
        "phone_verified": False,
    }
    with patch(
        "auth.adapters.users_services.verify_user", autospec=True, wraps=verify_user
    ) as fake_verify_user:
        callback_url, query = provider_auth(ssr_client, post_data, user_data)
        assert "error" not in query
        assert "access" in query
        assert "refresh" in query
        assert "username" in query
        assert query["next"] == ["/accept-project-invitation/token"]
        assert query["customValue"] == ["keep_it"]
        fake_verify_user.assert_not_awaited()


def test_redirect_to_provider_ok_invitation(ssr_client):
    post_data = {
        "callbackUrl": "/test",
        "acceptTermsOfService": True,
        "acceptPrivacyPolicy": True,
        "projectInvitationToken": "test",
        "workspaceInvitationToken": "test",
    }
    user_data = {
        "id": 0,
        "email": "test@email.com",
        "email_verified": True,
        "username": "",
        "first_name": "",
        "last_name": "",
        "phone": "",
        "phone_verified": False,
    }
    with patch(
        "auth.adapters.users_services.verify_user", autospec=True, wraps=verify_user
    ) as fake_verify_user:
        callback_url, query = provider_auth(ssr_client, post_data, user_data)
        assert "error" not in query
        assert "access" in query
        fake_verify_user.assert_awaited_once()
        assert (
            fake_verify_user.await_args.kwargs["project_invitation_token"]
            == fake_verify_user.call_args.kwargs["workspace_invitation_token"]
            == "test"
        )


def test_redirect_to_provider_untrusted(ssr_client):
    """we get an error if we try to use an unverified provider for an existing user"""
    user = f.sync_create_user()
    post_data = {
        "callbackUrl": "/test?customValue=keep_it&next=/accept-project-invitation/token",
        "acceptTermsOfService": True,
        "acceptPrivacyPolicy": True,
    }
    # untrusted scenario can happen if email is not verified
    user_data = {
        "id": 0,
        "email": user.email,
        "email_verified": False,
        "username": "",
        "first_name": "",
        "last_name": "",
        "phone": "",
        "phone_verified": False,
    }
    callback_url, query = provider_auth(ssr_client, post_data, user_data)
    assert (
        "error" not in query
    )  # for now, this error is not correctly handled, see https://codeberg.org/allauth/django-allauth/issues/4634
    assert "access" not in query
    assert "socialSessionKey" not in query

    # untrusted scenario can also happen if authentication by email is not enabled for this provider
    with override_settings(SOCIALACCOUNT_PROVIDERS={}):
        user_data["email_verified"] = True
        callback_url, query = provider_auth(ssr_client, post_data, user_data)
        assert "error" not in query
        assert "access" not in query
        assert "socialSessionKey" not in query


@override_settings(USER_EMAIL_ALLOWED_DOMAINS=["allowed.com"])
def test_redirect_to_provider_check_email_domain(ssr_client):
    post_data = {
        "callbackUrl": "/test",
        "acceptTermsOfService": True,
        "acceptPrivacyPolicy": True,
    }
    user_data = {
        "id": 0,
        "email": "test@email.com",
        "email_verified": True,
        "username": "",
        "first_name": "",
        "last_name": "",
        "phone": "",
        "phone_verified": False,
    }
    callback_url, query = provider_auth(ssr_client, post_data, user_data)
    assert query["error"] == ["permission_denied"]
    assert "socialSessionKey" not in query

    user_data["email"] = ""
    callback_url, query = provider_auth(ssr_client, post_data, user_data)
    assert not query

    user_data["email"] = "test@allowed.com"
    callback_url, query = provider_auth(ssr_client, post_data, user_data)
    assert "error" not in query
    assert "access" in query


def test_redirect_to_provider_cancelled(ssr_client):
    post_data = {
        "callbackUrl": "/test",
    }
    user_data = {
        "action": "cancel",
    }
    callback_url, query = provider_auth(ssr_client, post_data, user_data)
    assert query["error"] == ["cancelled"]
    assert "socialSessionKey" not in query


def test_redirect_to_provider_unverified(ssr_client):
    post_data = {
        "callbackUrl": "/test",
        "acceptTermsOfService": True,
        "acceptPrivacyPolicy": True,
    }
    user_data = {
        "id": 0,
        "email": "test@email.com",
        "email_verified": False,
        "username": "",
        "first_name": "",
        "last_name": "",
        "phone": "",
        "phone_verified": False,
    }
    with patch(
        "auth.adapters.users_services.verify_user", autospec=True, wraps=verify_user
    ) as fake_verify_user:
        callback_url, query = provider_auth(ssr_client, post_data, user_data)
        fake_verify_user.assert_not_awaited()
    assert query["error"] == ["unverified"]
    assert query["email"] == ["test@email.com"]
    assert "socialSessionKey" not in query


def test_redirect_to_provider_missing_terms_acceptance(ssr_client):
    post_data = {"callbackUrl": "/test", "acceptTermsOfService": True}
    user_data = {
        "id": 0,
        "email": "",
        "email_verified": False,
        "username": "",
        "first_name": "",
        "last_name": "",
        "phone": "",
        "phone_verified": False,
    }
    callback_url, query = provider_auth(ssr_client, post_data, user_data)
    assert query["error"] == ["missing_terms_acceptance"]
    assert "socialSessionKey" in query


def test_continue_signup_to_provider_invalid(ssr_client):
    response = ssr_client.post(
        f"/api/{settings.API_VERSION}/auth/provider/continue_signup",
        content_type="application/json",
    )
    assert response.status_code == 422, response.json()


def test_continue_signup_to_provider_notfound(ssr_client):
    data = {"socialSessionKey": "unknown"}
    response = ssr_client.post(
        f"/api/{settings.API_VERSION}/auth/provider/continue_signup",
        data=data,
        content_type="application/json",
    )
    assert response.status_code == 404, response.json()


def test_continue_signup_to_provider_ok(ssr_client):
    post_data = {"callbackUrl": "/test"}
    user_data = {
        "id": 0,
        "email": "test@email.com",
        "email_verified": True,
        "username": "",
        "first_name": "",
        "last_name": "",
        "phone": "",
        "phone_verified": False,
    }
    callback_url, query = provider_auth(ssr_client, post_data, user_data)
    assert query["error"] == ["missing_terms_acceptance"]
    socialSessionKey = query["socialSessionKey"][0]

    # terms still not accepted
    data = {"socialSessionKey": socialSessionKey}
    response = ssr_client.post(
        f"/api/{settings.API_VERSION}/auth/provider/continue_signup",
        data=data,
        content_type="application/json",
    )
    assert response.status_code == 200
    res = response.json()
    assert res["error"] == "missing_terms_acceptance"
    assert socialSessionKey == res["socialSessionKey"]

    # terms accepted
    data = {
        "socialSessionKey": socialSessionKey,
        "acceptTermsOfService": True,
        "acceptPrivacyPolicy": True,
    }
    response = ssr_client.post(
        f"/api/{settings.API_VERSION}/auth/provider/continue_signup",
        data=data,
        content_type="application/json",
    )
    assert response.status_code == 200
    res = response.json()
    assert "error" not in res
    assert "access" in res


def test_continue_signup_to_provider_unverified(ssr_client):
    post_data = {"callbackUrl": "/test"}
    user_data = {
        "id": 0,
        "email": "test@email.com",
        "email_verified": False,
        "username": "",
        "first_name": "",
        "last_name": "",
        "phone": "",
        "phone_verified": False,
    }
    callback_url, query = provider_auth(ssr_client, post_data, user_data)
    socialSessionKey = query["socialSessionKey"][0]

    data = {
        "socialSessionKey": socialSessionKey,
        "acceptTermsOfService": True,
        "acceptPrivacyPolicy": True,
    }
    response = ssr_client.post(
        f"/api/{settings.API_VERSION}/auth/provider/continue_signup",
        data=data,
        content_type="application/json",
    )
    assert response.status_code == 200
    res = response.json()
    assert res["error"] == "unverified"
    assert res["email"] == "test@email.com"
    assert res["socialSessionKey"] is None


def test_continue_signup_to_provider_untrusted(ssr_client):
    user = f.sync_create_user()
    post_data = {"callbackUrl": "/test"}
    user_data = {
        "id": 0,
        "email": user.email,
        "email_verified": False,
        "username": "",
        "first_name": "",
        "last_name": "",
        "phone": "",
        "phone_verified": False,
    }
    callback_url, query = provider_auth(ssr_client, post_data, user_data)
    socialSessionKey = query["socialSessionKey"][0]

    data = {
        "socialSessionKey": socialSessionKey,
        "acceptTermsOfService": True,
        "acceptPrivacyPolicy": True,
    }
    response = ssr_client.post(
        f"/api/{settings.API_VERSION}/auth/provider/continue_signup",
        data=data,
        content_type="application/json",
    )
    assert response.status_code == 424, response.json()
