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
from uuid import UUID

from django.db import migrations


def populate_jti_hex(apps, schema_editor):
    OutstandingToken = apps.get_model("token_blacklist", "OutstandingToken")

    db_alias = schema_editor.connection.alias
    for token in OutstandingToken.objects.using(db_alias).all():
        token.jti_hex = token.jti.hex
        token.save()


def reverse_populate_jti_hex(apps, schema_editor):  # pragma: no cover
    OutstandingToken = apps.get_model("token_blacklist", "OutstandingToken")

    db_alias = schema_editor.connection.alias
    for token in OutstandingToken.objects.using(db_alias).all():
        token.jti = UUID(hex=token.jti_hex)
        token.save()


class Migration(migrations.Migration):
    dependencies = [
        ("token_blacklist", "0002_outstandingtoken_jti_hex"),
    ]

    operations = [
        migrations.RunPython(populate_jti_hex, reverse_populate_jti_hex),
    ]
