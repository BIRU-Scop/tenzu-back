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

from asgiref.sync import sync_to_async

from .base import Factory, factory


class UserFactory(Factory):
    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@email.com")
    full_name = factory.Sequence(lambda n: f"Test User {n}")
    color = factory.Faker("pyint", min_value=1, max_value=8)
    password = factory.django.Password("123123")
    is_active = True

    class Meta:
        model = "users.User"


@sync_to_async
def create_user(**kwargs):
    return UserFactory.create(**kwargs)


def sync_create_user(**kwargs):
    return UserFactory.create(**kwargs)


def build_user(**kwargs):
    return UserFactory.build(**kwargs)


class AuthDataFactory(Factory):
    user = factory.SubFactory("tests.utils.factories.UserFactory")
    key = "google"
    value = "103576024907356273435"

    class Meta:
        model = "users.AuthData"


def build_auth_data(**kwargs):
    return AuthDataFactory.build(**kwargs)


@sync_to_async
def create_auth_data(**kwargs):
    return AuthDataFactory.create(**kwargs)
