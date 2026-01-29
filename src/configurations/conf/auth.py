# -*- coding: utf-8 -*-
# Copyright (C) 2024-2026 BIRU
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
from datetime import timedelta
from enum import StrEnum
from typing import Annotated, Literal, Self

import ldap
from django.utils.module_loading import import_string
from django_auth_ldap.config import (
    LDAPGroupType as DjangoAuthLDAPGroupType,
)
from django_auth_ldap.config import (
    LDAPSearch,
    LDAPSearchUnion,
)
from django_auth_ldap.config import (
    LDAPSettings as DjangoAuthLDAPSettings,
)
from pydantic import (
    AfterValidator,
    AnyUrl,
    BaseModel,
    Field,
    PositiveInt,
    field_validator,
    model_validator,
)

from ninja_jwt.backends import AllowedAlgorithmsType


class TokensSettings(BaseModel):
    SIGNING_KEY: str
    ALGORITHM: AllowedAlgorithmsType = "HS512"
    VERIFYING_KEY: str = ""
    AUDIENCE: str | None = None
    ISSUER: str | None = None
    ACCESS_TOKEN_LIFETIME: timedelta = timedelta(minutes=5)
    REFRESH_TOKEN_LIFETIME: timedelta = timedelta(hours=4)

    TOKEN_TYPE_CLAIM: str = "token_type"
    JTI_CLAIM: str = "jti"
    USER_ID_FIELD: str = "id"
    USER_ID_CLAIM: str = "user_id"


class AccountSettings(BaseModel):
    SOCIALACCOUNT_REQUESTS_TIMEOUT: int = 5
    SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT: bool = True
    SOCIALACCOUNT_PROVIDERS: dict[str, dict] = Field(
        default_factory=dict
    )  # you can also use the admin app to dynamically add SocialApp instead, see https://docs.allauth.org/en/latest/socialaccount/provider_configuration.html
    SOCIALAPPS_PROVIDERS: list[str] = Field(default_factory=list)
    # user
    USER_EMAIL_ALLOWED_DOMAINS: list[str] = Field(
        default_factory=list,
    )
    VERIFY_USER_TOKEN_LIFETIME: timedelta = Field(
        default=timedelta(days=4),
    )
    RESET_PASSWORD_TOKEN_LIFETIME: timedelta = Field(
        default=timedelta(hours=2),
    )


class LDAPActivation(StrEnum):
    DONT_USE = "no"  # Don't use the LDAP backend to authenticate users
    ONLY_USE = "strict"  # Only use the LDAP backend to authenticate user. Prevent new user creation
    CAN_USE = "lax"  # Try to authenticate user using either the LDAP backend, fallback to the Django user model
    # /!\ Lax mode do not handle username conflict with db users, account takeover from ldap is possible with this mode
    # use this mode with caution


def _option_exists(v: int) -> int:
    if v not in ldap.OPT_NAMES_DICT.keys():
        raise ValueError(
            f"Value {v} is not a valid LDAP option, only use available ldap.OPT_* values"
        )
    return v


LDAPOption = Annotated[PositiveInt, AfterValidator(_option_exists)]


def _has_user_placeholder(v: str) -> str:
    if "%(user)s" not in v:
        raise ValueError(f"Value {v} is missing the user placeholder '%(user)s'")
    return v


LDAPUserFilter = Annotated[str, AfterValidator(_has_user_placeholder)]


class LDAPSearchParams(BaseModel):
    base_dn: str
    scope: Literal[
        ldap.SCOPE_BASE, ldap.SCOPE_ONELEVEL, ldap.SCOPE_SUBORDINATE, ldap.SCOPE_SUBTREE
    ]
    filterstr: str

    def to_ldap_search(self) -> LDAPSearch:
        return LDAPSearch(
            base_dn=self.base_dn,
            scope=self.scope,
            filterstr=self.filterstr,
        )


class LDAPUserSearchParams(LDAPSearchParams):
    filterstr: LDAPUserFilter


class LDAPGroupType(BaseModel):
    class_name: Literal[
        "django_auth_ldap.config.PosixGroupType",
        "django_auth_ldap.config.MemberDNGroupType",
        "django_auth_ldap.config.NestedMemberDNGroupType",
        "django_auth_ldap.config.GroupOfNamesType",
        "django_auth_ldap.config.NestedGroupOfNamesType",
        "django_auth_ldap.config.GroupOfUniqueNamesType",
        "django_auth_ldap.config.NestedGroupOfUniqueNamesType",
        "django_auth_ldap.config.ActiveDirectoryGroupType",
        "django_auth_ldap.config.NestedActiveDirectoryGroupType",
        "django_auth_ldap.config.OrganizationalRoleGroupType",
        "django_auth_ldap.config.NestedOrganizationalRoleGroupType",
    ]
    member_attr: str | None = None
    name_attr: str = "cn"

    @property
    def is_member_attr_required(self):
        return self.class_name in {
            "django_auth_ldap.config.MemberDNGroupType",
            "django_auth_ldap.config.NestedMemberDNGroupType",
        }

    @model_validator(mode="after")
    def check_required_member_attr(self) -> Self:
        if self.is_member_attr_required:
            if self.member_attr is None:
                raise ValueError(
                    f"member_attr is needed for group type {self.class_name}"
                )
        return self

    def to_instance(self) -> DjangoAuthLDAPGroupType:
        group_class = import_string(self.class_name)
        instance_kwargs = {"name_attr": self.name_attr}
        if self.is_member_attr_required:
            instance_kwargs["member_attr"] = self.member_attr
        return group_class(**instance_kwargs)


class LDAPSettings(BaseModel):
    ACTIVATION: LDAPActivation = LDAPActivation.DONT_USE
    SERVER_URI: Annotated[AnyUrl, AfterValidator(str)] = (
        DjangoAuthLDAPSettings.defaults["SERVER_URI"]
    )
    CONNECTION_OPTIONS: dict[LDAPOption, str | int] = DjangoAuthLDAPSettings.defaults[
        "CONNECTION_OPTIONS"
    ]
    GLOBAL_OPTIONS: dict[LDAPOption, str | int] | None = None
    BIND_AS_AUTHENTICATING_USER: bool = DjangoAuthLDAPSettings.defaults[
        "BIND_AS_AUTHENTICATING_USER"
    ]
    BIND_DN: str = DjangoAuthLDAPSettings.defaults["BIND_DN"]
    BIND_PASSWORD: str = DjangoAuthLDAPSettings.defaults["BIND_PASSWORD"]
    START_TLS: bool = DjangoAuthLDAPSettings.defaults["START_TLS"]

    USER_SEARCH: list[LDAPUserSearchParams] = Field(default=[], validate_default=True)
    USER_DN_TEMPLATE: LDAPUserFilter | None = DjangoAuthLDAPSettings.defaults[
        "USER_DN_TEMPLATE"
    ]

    GROUP_SEARCH: LDAPSearchParams | None = None
    GROUP_TYPE: LDAPGroupType | None = None
    REQUIRE_GROUP: str | None = DjangoAuthLDAPSettings.defaults["REQUIRE_GROUP"]
    DENY_GROUP: str | None = DjangoAuthLDAPSettings.defaults["DENY_GROUP"]

    USER_ATTR_MAP: dict[str, str] = DjangoAuthLDAPSettings.defaults["USER_ATTR_MAP"]
    USER_QUERY_FIELD: str | None = DjangoAuthLDAPSettings.defaults["USER_QUERY_FIELD"]
    USER_FLAGS_BY_GROUP: dict[str, str | list[str]] = DjangoAuthLDAPSettings.defaults[
        "USER_FLAGS_BY_GROUP"
    ]
    ALWAYS_UPDATE_USER: bool = DjangoAuthLDAPSettings.defaults["ALWAYS_UPDATE_USER"]
    REFRESH_DN_ON_BIND: bool = DjangoAuthLDAPSettings.defaults["REFRESH_DN_ON_BIND"]
    CACHE_TIMEOUT: PositiveInt = DjangoAuthLDAPSettings.defaults["CACHE_TIMEOUT"]

    @model_validator(mode="after")
    def assert_email_can_be_fetched(self) -> Self:
        if (
            self.ACTIVATION != LDAPActivation.DONT_USE
            and "email" not in self.USER_ATTR_MAP.keys()
        ):
            raise ValueError(
                "You need to set a mapping in USER_ATTR_MAP to retrieve users' email field"
            )
        return self

    @field_validator("USER_SEARCH", mode="after")
    @classmethod
    def create_ldap_user_search(
        cls, value: list[LDAPSearchParams]
    ) -> LDAPSearchUnion | LDAPSearch | None:
        if not value:
            return None
        search_queries = [params.to_ldap_search() for params in value]
        if len(search_queries) == 1:
            return search_queries[0]
        return LDAPSearchUnion(*search_queries)

    @field_validator("GROUP_SEARCH", mode="after")
    @classmethod
    def create_ldap_group_search(cls, value: LDAPSearchParams) -> LDAPSearch | None:
        if not value:
            return None
        return value.to_ldap_search()

    @field_validator("GROUP_TYPE", mode="after")
    @classmethod
    def create_ldap_group_type(
        cls, value: LDAPGroupType
    ) -> DjangoAuthLDAPGroupType | None:
        if not value:
            return None
        return value.to_instance()
