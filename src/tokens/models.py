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

#
#
# The code is partially taken (and modified) from djangorestframework-simplejwt v. 4.7.1
# (https://github.com/jazzband/djangorestframework-simplejwt/tree/5997c1aee8ad5182833d6b6759e44ff0a704edb4)
# that is licensed under the following terms:
#
#   Copyright 2017 David Sanders
#
#   Permission is hereby granted, free of charge, to any person obtaining a copy of
#   this software and associated documentation files (the "Software"), to deal in
#   the Software without restriction, including without limitation the rights to
#   use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
#   of the Software, and to permit persons to whom the Software is furnished to do
#   so, subject to the following conditions:
#
#   The above copyright notice and this permission notice shall be included in all
#   copies or substantial portions of the Software.
#
#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#   AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#   LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#   OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#   SOFTWARE.

from base.db import models


class OutstandingToken(models.BaseModel):
    content_type = models.ForeignKey(models.ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.UUIDField(null=True, blank=True)
    content_object = models.GenericForeignKey("content_type", "object_id")

    jti = models.CharField(unique=True, max_length=255)
    token_type = models.TextField()
    token = models.TextField()

    created_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField()

    class Meta:
        verbose_name = "outstanding token"
        verbose_name_plural = "outstanding tokens"
        indexes = [
            models.Index(fields=["content_type", "object_id", "token_type"]),
            models.Index(fields=["jti"]),
            models.Index(fields=["expires_at"]),
        ]
        ordering = ("content_type", "object_id", "token_type")

    def __str__(self) -> str:
        return f"Token for {self.content_object} ({type(self.content_object)}) [{self.jti}]"

    def __repr__(self) -> str:
        return f"<OutstandingToken {type(self.content_object)} [{self.jti}]>"


class DenylistedToken(models.BaseModel):
    token = models.OneToOneField(OutstandingToken, on_delete=models.CASCADE)

    denylisted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "denylisted token"
        verbose_name_plural = "denylisted tokens"
        indexes = [
            models.Index(fields=["token"]),
        ]

    def __str__(self) -> str:
        return f"Denylisted token for {self.token.content_object} ({type(self.token.content_object)})"

    def __repr__(self) -> str:
        return f"<DenylistedToken {self.token}>"
