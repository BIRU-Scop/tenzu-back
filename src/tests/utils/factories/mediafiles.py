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


class MediafileFactory(Factory):
    name = factory.Sequence(lambda n: f"test-file-{n}.png")
    file = factory.django.ImageField(format="PNG")
    content_type = "image/png"
    size = 145
    project = factory.SubFactory("tests.utils.factories.ProjectFactory")

    class Meta:
        model = "mediafiles.Mediafile"


@sync_to_async
def create_mediafile(**kwargs):
    return MediafileFactory.create(**kwargs)


def build_mediafile(**kwargs):
    return MediafileFactory.build(**kwargs)
