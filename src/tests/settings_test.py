# -*- coding: utf-8 -*-
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


from configurations.settings import *  # noqa
from configurations.settings import INSTALLED_APPS

DEBUG = True

MEDIA_ROOT = "/tmp/tenzu/media"
STATIC_ROOT = "/tmp/tenzu/static"

INSTALLED_APPS = [*INSTALLED_APPS, "tests.utils.samples.occ"]
if "allauth.socialaccount.providers.dummy" not in INSTALLED_APPS:
    INSTALLED_APPS = [*INSTALLED_APPS, "allauth.socialaccount.providers.dummy"]

DEBUG_PROPAGATE_EXCEPTIONS = (True,)
SITE_ID = 1
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
NINJA_JWT = {
    "BLACKLIST_AFTER_ROTATION": True,
    "SIGNING_KEY": "not very secret in tests",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

USER_EMAIL_ALLOWED_DOMAINS = []

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

REQUIRED_TERMS = True
MAX_UPLOAD_FILE_SIZE = 1 * 1024  # 1 KB
