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

from unittest.mock import patch

from projects.projects import serializers
from tests.utils import factories as f

#######################################################
# ProjectLogoMixin
#######################################################


def test_project_logo_mixin_serializer_with_logo():
    project = f.build_project(logo=f.build_image_file())

    with (
        patch(
            "projects.projects.services.get_logo_small_thumbnail_url", autospec=True
        ) as fake_get_logo_small,
        patch(
            "projects.projects.services.get_logo_large_thumbnail_url", autospec=True
        ) as fake_get_logo_large,
    ):
        fake_get_logo_small.return_value = "small_logo.png"
        fake_get_logo_large.return_value = "large_logo.png"

        data = serializers.ProjectLogoMixin(logo=project.logo)

        assert data.logo == project.logo
        assert data.logo_small == "small_logo.png"
        assert data.logo_large == "large_logo.png"

        fake_get_logo_small.assert_awaited_once_with(project.logo)
        fake_get_logo_large.assert_awaited_once_with(project.logo)


def test_project_logo_mixin_serializer_without_logo():
    with (
        patch(
            "projects.projects.services.get_logo_small_thumbnail_url", autospec=True
        ) as fake_get_logo_small,
        patch(
            "projects.projects.services.get_logo_large_thumbnail_url", autospec=True
        ) as fake_get_logo_large,
    ):
        data = serializers.ProjectLogoMixin(logo=None)

        assert data.logo is None
        assert data.logo_small is None
        assert data.logo_large is None

        fake_get_logo_small.assert_not_awaited()
        fake_get_logo_large.assert_not_awaited()
