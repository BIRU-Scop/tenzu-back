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

import re
from typing import Any, Iterable

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, AnonymousUser, UserManager
from django.core.validators import MaxValueValidator, RegexValidator
from django.db import models

from base.db.models import BaseModel, LowerCharField, LowerEmailField, LowerSlugField
from base.utils.slug import generate_int_suffix, slugify_uniquely
from commons.colors import NUM_COLORS, generate_random_color

type AnyUser = AnonymousUser | "User" | AbstractBaseUser


def default_language() -> str:
    return settings.LANGUAGE_CODE


class User(BaseModel, AbstractBaseUser):
    username = LowerCharField(
        max_length=255,
        null=False,
        blank=False,
        unique=True,
        verbose_name="username",
        help_text="Required. 255 characters or fewer. Letters, numbers and /./-/_ characters",
        validators=[
            RegexValidator(
                re.compile(r"^[\w.-]+$"), "Enter a valid username.", "invalid"
            )
        ],
    )
    email = LowerEmailField(
        max_length=255,
        null=False,
        blank=False,
        unique=True,
        verbose_name="email address",
    )
    color = models.IntegerField(
        null=False,
        blank=True,
        default=generate_random_color,
        verbose_name="color",
        validators=[MaxValueValidator(NUM_COLORS)],
    )
    is_active = models.BooleanField(
        null=False,
        blank=True,
        default=False,
        verbose_name="active",
        help_text="Designates whether this user should be treated as active.",
    )
    is_superuser = models.BooleanField(
        null=False,
        blank=True,
        default=False,
        verbose_name="superuser status",
        help_text="Designates that this user has all permissions without "
        "explicitly assigning them.",
    )
    full_name = models.CharField(
        max_length=256, null=False, blank=True, default="", verbose_name="full name"
    )
    accepted_terms = models.BooleanField(
        null=False, blank=False, default=True, verbose_name="accepted terms"
    )
    lang = models.CharField(
        max_length=20,
        null=False,
        blank=False,
        default=default_language,
        verbose_name="language",
    )
    date_joined = models.DateTimeField(
        null=False, blank=False, auto_now_add=True, verbose_name="date joined"
    )
    date_verification = models.DateTimeField(
        null=True, blank=True, default=None, verbose_name="date verification"
    )

    EMAIL_FIELD = "email"
    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    objects = UserManager()

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"
        indexes = [
            models.Index(fields=["username"]),
            models.Index(fields=["email"]),
        ]
        ordering = ["username"]

    def __str__(self) -> str:
        return self.username

    def __repr__(self) -> str:
        return f"<User {self.username}>"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self.username:
            self.username = slugify_uniquely(
                value=self.email.split("@")[0],
                slugfield="username",
                model=self.__class__,
                generate_suffix=generate_int_suffix(),
                use_always_suffix=False,
                template="{base}{suffix}",
            )

        super().save(*args, **kwargs)

    def get_short_name(self) -> str:
        return self.username

    def get_full_name(self) -> str:
        return self.full_name or self.username

    @property
    def is_staff(self) -> bool:
        return self.is_superuser

    def has_perm(self, perm: str, obj: AnyUser | None = None) -> bool:
        return self.is_active and self.is_superuser

    def has_perms(self, perm_list: Iterable[str], obj: AnyUser | None = None) -> bool:
        return self.is_active and self.is_superuser

    def has_module_perms(self, app_label: str) -> bool:
        return self.is_active and self.is_superuser


class AuthData(BaseModel):
    user = models.ForeignKey(
        "users.User",
        null=False,
        blank=False,
        related_name="auth_data",
        on_delete=models.CASCADE,
    )
    key = LowerSlugField(max_length=50, null=False, blank=False, verbose_name="key")
    value = models.CharField(
        max_length=300, null=False, blank=False, verbose_name="value"
    )
    extra = models.JSONField(null=True, blank=True, verbose_name="extra")

    class Meta:
        verbose_name = "user's auth data"
        verbose_name_plural = "user's auth data"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "key"], name="%(app_label)s_%(class)s_unique_user_key"
            ),
        ]
        indexes = [
            models.Index(fields=["user", "key"]),
        ]
        ordering = ["user", "key"]

    def __str__(self) -> str:
        return f"{self.key}: {self.value}"

    def __repr__(self) -> str:
        return f"<AuthData {self.user} {self.key}>"
