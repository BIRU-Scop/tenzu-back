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
from urllib.parse import urljoin

from django.conf import settings
from django.urls import reverse_lazy
from ninja import Schema

from attachments.serializers import AttachmentSerializer
from base.serializers import FileField


class StoryAttachmentSerializer(AttachmentSerializer):
    file: FileField

    @staticmethod
    def resolve_file(obj):
        return urljoin(
            str(settings.BACKEND_URL),
            str(
                reverse_lazy(
                    "api-v1:project.story.attachments.file",
                    kwargs={
                        "project_id": obj.content_object.project.b64id,
                        "ref": obj.content_object.ref,
                        "attachment_id": obj.b64id,
                    },
                )
            ),
        )


class StreamResponseSchema(Schema):
    detail: str
