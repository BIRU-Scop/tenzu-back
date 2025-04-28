# -*- coding: utf-8 -*-
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
from dataclasses import dataclass

import pytest
from django.contrib.auth.models import AnonymousUser

from base.utils import datetime
from base.utils.datetime import aware_utcnow
from commons.exceptions import api as ex
from permissions import (
    AllowAny,
    And,
    DenyAll,
    IsAuthenticated,
    IsNotDeleted,
    IsRelatedToTheUser,
    IsSuperUser,
    Not,
    Or,
    check_permissions,
)
from tests.utils import factories as f


@dataclass
class DummyDeletedAt:
    deleted_at: datetime.datetime | None


#####################################################
# check_permissions (is_authorized)
#####################################################


async def test_check_permission_allow_any():
    user1 = f.build_user()
    permissions = AllowAny()

    # always granted permissions
    assert (
        await check_permissions(permissions=permissions, user=user1, obj=None) is None
    )


async def test_check_permission_deny_all():
    user = f.build_user()
    permissions = DenyAll()

    # never granted permissions
    with pytest.raises(ex.ForbiddenError):
        await check_permissions(permissions=permissions, user=user, obj=None)


async def test_check_permission_is_superuser():
    user1 = f.build_user(is_superuser=True)
    user2 = f.build_user(is_superuser=False)
    permissions = IsSuperUser()

    assert await permissions.is_authorized(user=user1, obj=None)
    assert not (await permissions.is_authorized(user=user2, obj=None))
    # superuser always is authorised
    permissions = DenyAll()
    assert (
        await check_permissions(permissions=permissions, user=user1, obj=None) is None
    )
    with pytest.raises(ex.ForbiddenError):
        await check_permissions(permissions=permissions, user=user2, obj=None)


async def test_check_permission_is_authenticated():
    user1 = f.build_user()
    user2 = AnonymousUser()
    permissions = IsAuthenticated()

    # User.is_authenticated is always True
    assert (
        await check_permissions(permissions=permissions, user=user1, obj=None) is None
    )
    # AnonymousUser.is_authenticated is always False
    with pytest.raises(ex.AuthorizationError):
        await check_permissions(permissions=permissions, user=user2, obj=None)


async def test_check_permission_is_related_to_the_user():
    user1 = f.build_user()
    user2 = f.build_user()
    permissions = IsRelatedToTheUser()
    DummyRelated1 = type("DummyRelated1", (), {"user": user1})
    DummyRelated2 = type("DummyRelated2", (), {"user": user2})
    DummyRelated3 = type("DummyRelated3", (), {"user": None})
    DummyRelated4 = type("DummyRelated4", (), {"field": user1})

    with pytest.raises(ex.ForbiddenError):
        await check_permissions(permissions=permissions, user=user1, obj=None)

    assert (
        await check_permissions(permissions=permissions, user=user1, obj=DummyRelated1)
        is None
    )
    with pytest.raises(ex.ForbiddenError):
        await check_permissions(permissions=permissions, user=user1, obj=DummyRelated2)
    with pytest.raises(ex.ForbiddenError):
        await check_permissions(permissions=permissions, user=user1, obj=DummyRelated3)
    permissions = IsRelatedToTheUser("field")
    assert (
        await check_permissions(permissions=permissions, user=user1, obj=DummyRelated4)
        is None
    )


async def test_check_permission_is_not_deleted():
    user1 = AnonymousUser()
    permissions = IsNotDeleted()

    assert (
        await check_permissions(permissions=permissions, user=user1, obj=None) is None
    )
    assert (
        await check_permissions(permissions=permissions, user=user1, obj=object())
        is None
    )
    assert (
        await check_permissions(
            permissions=permissions, user=user1, obj=DummyDeletedAt(deleted_at=None)
        )
        is None
    )
    with pytest.raises(ex.ForbiddenError):
        await check_permissions(
            permissions=permissions,
            user=user1,
            obj=DummyDeletedAt(deleted_at=aware_utcnow()),
        )


#############################################
# PermissionOperators (Not/Or/And)
#############################################


@pytest.mark.parametrize(
    [
        "permission_true_and",
        "permission_false_and",
        "permission_true_all_or",
        "permission_true_some_or",
        "permission_false_or",
        "permission_true_not",
        "permission_false_not",
        "permission_true_all_together",
        "permission_false_all_together",
    ],
    [
        [
            IsNotDeleted() & AllowAny(),
            IsNotDeleted() & AllowAny() & IsSuperUser(),
            IsNotDeleted() | AllowAny(),
            IsNotDeleted() | AllowAny() | IsSuperUser(),
            IsSuperUser() | DenyAll(),
            ~DenyAll(),
            ~AllowAny(),
            ~((IsNotDeleted() | AllowAny()) & (IsNotDeleted() & DenyAll())),
            ~((IsNotDeleted() | AllowAny()) | (IsNotDeleted() & DenyAll())),
        ],
        [
            And(IsNotDeleted(), AllowAny()),
            And(IsNotDeleted(), AllowAny(), IsSuperUser()),
            Or(IsNotDeleted(), AllowAny()),
            Or(IsNotDeleted(), AllowAny(), IsSuperUser()),
            Or(IsSuperUser(), DenyAll()),
            Not(DenyAll()),
            Not(AllowAny()),
            Not(And(Or(IsNotDeleted(), AllowAny()), And(IsNotDeleted(), DenyAll()))),
            Not(Or(Or(IsNotDeleted(), AllowAny()), And(IsNotDeleted(), DenyAll()))),
        ],
    ],
)
async def test_check_permission_operators(
    permission_true_and,
    permission_false_and,
    permission_true_all_or,
    permission_true_some_or,
    permission_false_or,
    permission_true_not,
    permission_false_not,
    permission_true_all_together,
    permission_false_all_together,
):
    user = f.build_user()
    obj = object()

    assert (
        await check_permissions(permissions=permission_true_and, user=user, obj=obj)
        is None
    )
    with pytest.raises(ex.ForbiddenError):
        await check_permissions(permissions=permission_false_and, user=user, obj=obj)
    assert (
        await check_permissions(permissions=permission_true_all_or, user=user, obj=obj)
        is None
    )
    assert (
        await check_permissions(permissions=permission_true_some_or, user=user, obj=obj)
        is None
    )
    with pytest.raises(ex.ForbiddenError):
        await check_permissions(permissions=permission_false_or, user=user, obj=obj)
    assert (
        await check_permissions(permissions=permission_true_not, user=user, obj=obj)
        is None
    )
    with pytest.raises(ex.ForbiddenError):
        await check_permissions(permissions=permission_false_not, user=user, obj=obj)
    assert (
        await check_permissions(
            permissions=permission_true_all_together, user=user, obj=obj
        )
        is None
    )
    with pytest.raises(ex.ForbiddenError):
        await check_permissions(
            permissions=permission_false_all_together, user=user, obj=obj
        )
