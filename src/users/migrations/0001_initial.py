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

import django.contrib.auth.models
import django.contrib.postgres.fields.jsonb
import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import base.db.models
import base.db.models.fields
import base.utils.colors
import users.models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="User",
            fields=[
                ("password", models.CharField(max_length=128, verbose_name="password")),
                (
                    "last_login",
                    models.DateTimeField(blank=True, null=True, verbose_name="last login"),
                ),
                (
                    "id",
                    models.UUIDField(
                        blank=True,
                        default=base.db.models.uuid_generator,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "username",
                    base.db.models.fields.LowerCharField(
                        help_text="Required. 255 characters or fewer. Letters, numbers and /./-/_ characters",
                        max_length=255,
                        unique=True,
                        validators=[
                            django.core.validators.RegexValidator(
                                re.compile("^[\\w.-]+$"),
                                "Enter a valid username.",
                                "invalid",
                            )
                        ],
                        verbose_name="username",
                    ),
                ),
                (
                    "email",
                    base.db.models.fields.LowerEmailField(max_length=255, unique=True, verbose_name="email address"),
                ),
                (
                    "color",
                    models.IntegerField(
                        blank=True,
                        default=base.utils.colors.generate_random_color,
                        verbose_name="color",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        blank=True,
                        default=False,
                        help_text="Designates whether this user should be treated as active.",
                        verbose_name="active",
                    ),
                ),
                (
                    "is_superuser",
                    models.BooleanField(
                        blank=True,
                        default=False,
                        help_text="Designates that this user has all permissions without explicitly assigning them.",
                        verbose_name="superuser status",
                    ),
                ),
                (
                    "full_name",
                    models.CharField(blank=True, max_length=256, null=True, verbose_name="full name"),
                ),
                (
                    "accepted_terms",
                    models.BooleanField(default=True, verbose_name="accepted terms"),
                ),
                (
                    "lang",
                    models.CharField(
                        default=users.models.default_language,
                        max_length=20,
                        verbose_name="language",
                    ),
                ),
                (
                    "date_joined",
                    models.DateTimeField(auto_now_add=True, verbose_name="date joined"),
                ),
                (
                    "date_verification",
                    models.DateTimeField(
                        blank=True,
                        default=None,
                        null=True,
                        verbose_name="date verification",
                    ),
                ),
            ],
            options={
                "verbose_name": "user",
                "verbose_name_plural": "users",
                "ordering": ["username"],
            },
            managers=[
                ("objects", django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name="AuthData",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        blank=True,
                        default=base.db.models.uuid_generator,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("key", base.db.models.fields.LowerSlugField(verbose_name="key")),
                ("value", models.CharField(max_length=300, verbose_name="value")),
                (
                    "extra",
                    django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True, verbose_name="extra"),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="auth_data",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "user's auth data",
                "verbose_name_plural": "user's auth data",
                "ordering": ["user", "key"],
            },
        ),
        migrations.AddIndex(
            model_name="user",
            index=models.Index(fields=["username"], name="users_user_usernam_65d164_idx"),
        ),
        migrations.AddIndex(
            model_name="user",
            index=models.Index(fields=["email"], name="users_user_email_6f2530_idx"),
        ),
        migrations.AddIndex(
            model_name="authdata",
            index=models.Index(fields=["user", "key"], name="users_authd_user_id_d24d4c_idx"),
        ),
        migrations.AddConstraint(
            model_name="authdata",
            constraint=models.UniqueConstraint(fields=("user", "key"), name="users_authdata_unique_user_key"),
        ),
    ]
