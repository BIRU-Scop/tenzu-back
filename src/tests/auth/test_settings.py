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

import os

import ldap
import pytest
from django_auth_ldap.config import (
    LDAPSearch,
    LDAPSearchUnion,
    NestedMemberDNGroupType,
    PosixGroupType,
)
from pydantic import ValidationError

from configurations.conf import Settings


@pytest.fixture(scope="module", autouse=True)
def reset_auth_ldap_environs():
    ldap_config = {key for key in os.environ if key.startswith("TENZU_LDAP__")}
    for key in ldap_config:
        del os.environ[key]


def test_default():
    settings = Settings(_env_parse_none_str="null")
    assert settings.LDAP.USER_SEARCH is None
    assert settings.LDAP.GROUP_SEARCH is None
    assert settings.LDAP.GROUP_TYPE is None


def test_connection_options():
    invalid_option = max(ldap.OPT_NAMES_DICT.keys()) + 1
    os.environ["TENZU_LDAP__CONNECTION_OPTIONS"] = f'{{"{invalid_option}": 0}}'
    with pytest.raises(ValidationError):
        Settings(_env_parse_none_str="null")
    os.environ["TENZU_LDAP__CONNECTION_OPTIONS"] = (
        f'{{"{ldap.OPT_REFERRALS}": {ldap.OPT_OFF}}}'
    )
    Settings(_env_parse_none_str="null")
    del os.environ["TENZU_LDAP__CONNECTION_OPTIONS"]


def test_user_dn_template():
    os.environ["TENZU_LDAP__USER_DN_TEMPLATE"] = "not_ok"
    with pytest.raises(ValidationError):
        Settings(_env_parse_none_str="null")
    os.environ["TENZU_LDAP__USER_DN_TEMPLATE"] = "ok_%(user)s"
    Settings(_env_parse_none_str="null")
    del os.environ["TENZU_LDAP__USER_DN_TEMPLATE"]


def test_user_search():
    os.environ["TENZU_LDAP__USER_SEARCH"] = (
        f'[{{"base_dn": "test", "scope": {ldap.SCOPE_SUBTREE}, "filterstr": "not_ok"}}]'
    )
    with pytest.raises(ValidationError):
        Settings(_env_parse_none_str="null")
    os.environ["TENZU_LDAP__USER_SEARCH"] = (
        f'[{{"base_dn": "test", "scope": {ldap.SCOPE_SUBTREE}, "filterstr": "ok_%(user)s"}}]'
    )
    settings = Settings(_env_parse_none_str="null")
    assert (
        settings.LDAP.USER_SEARCH.__dict__
        == LDAPSearch("test", ldap.SCOPE_SUBTREE, "ok_%(user)s").__dict__
    )
    os.environ["TENZU_LDAP__USER_SEARCH"] = (
        f'[{{"base_dn": "test", "scope": {ldap.SCOPE_SUBTREE}, "filterstr": "ok_%(user)s"}}, {{"base_dn": "test2", "scope": {ldap.SCOPE_ONELEVEL}, "filterstr": "ok_%(user)s"}}]'
    )
    settings = Settings(_env_parse_none_str="null")
    assert isinstance(settings.LDAP.USER_SEARCH, LDAPSearchUnion)
    for search, control_search in zip(
        settings.LDAP.USER_SEARCH.searches,
        (
            LDAPSearch("test", ldap.SCOPE_SUBTREE, "ok_%(user)s"),
            LDAPSearch("test2", ldap.SCOPE_ONELEVEL, "ok_%(user)s"),
        ),
    ):
        assert search.__dict__ == control_search.__dict__
    del os.environ["TENZU_LDAP__USER_SEARCH"]


def test_group_search():
    invalid_scope = (
        max(
            ldap.SCOPE_BASE,
            ldap.SCOPE_ONELEVEL,
            ldap.SCOPE_SUBORDINATE,
            ldap.SCOPE_SUBTREE,
        )
        + 1
    )
    os.environ["TENZU_LDAP__GROUP_SEARCH"] = (
        f'{{"base_dn": "test", "scope": {invalid_scope}, "filterstr": "test"}}'
    )
    with pytest.raises(ValidationError):
        Settings(_env_parse_none_str="null")
    os.environ["TENZU_LDAP__GROUP_SEARCH"] = (
        f'{{"base_dn": "test", "scope": {ldap.SCOPE_SUBORDINATE}, "filterstr": "test"}}'
    )
    settings = Settings(_env_parse_none_str="null")
    assert (
        settings.LDAP.GROUP_SEARCH.__dict__
        == LDAPSearch("test", ldap.SCOPE_SUBORDINATE, "test").__dict__
    )
    del os.environ["TENZU_LDAP__GROUP_SEARCH"]


def test_group_type():
    os.environ["TENZU_LDAP__GROUP_TYPE"] = (
        '{"class_name": "invalid", "name_attr": "test"}'
    )
    with pytest.raises(ValidationError):
        Settings(_env_parse_none_str="null")
    os.environ["TENZU_LDAP__GROUP_TYPE"] = (
        '{"class_name": "django_auth_ldap.config.NestedMemberDNGroupType", "name_attr": "test"}'
    )
    with pytest.raises(ValidationError):
        Settings(_env_parse_none_str="null")
    os.environ["TENZU_LDAP__GROUP_TYPE"] = (
        '{"class_name": "django_auth_ldap.config.PosixGroupType", "name_attr": "test"}'
    )
    settings = Settings(_env_parse_none_str="null")
    control_value = PosixGroupType("test")
    assert settings.LDAP.GROUP_TYPE.__dict__ == control_value.__dict__
    assert settings.LDAP.GROUP_TYPE.__class__ == control_value.__class__
    os.environ["TENZU_LDAP__GROUP_TYPE"] = (
        '{"class_name": "django_auth_ldap.config.NestedMemberDNGroupType", "member_attr": "test"}'
    )
    settings = Settings(_env_parse_none_str="null")
    control_value = NestedMemberDNGroupType(member_attr="test")
    assert settings.LDAP.GROUP_TYPE.__dict__ == control_value.__dict__
    assert settings.LDAP.GROUP_TYPE.__class__ == control_value.__class__
    del os.environ["TENZU_LDAP__GROUP_TYPE"]


def test_user_attr_map():
    os.environ["TENZU_LDAP__ACTIVATION"] = "lax"
    with pytest.raises(ValidationError):
        Settings(_env_parse_none_str="null")
    os.environ["TENZU_LDAP__USER_ATTR_MAP"] = '{"email": "eMail"}'
    Settings(_env_parse_none_str="null")
    del os.environ["TENZU_LDAP__ACTIVATION"]
    del os.environ["TENZU_LDAP__USER_ATTR_MAP"]
