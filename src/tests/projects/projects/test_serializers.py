# -*- coding: utf-8 -*-
# Copyright (C) 2024-2026 BIRU
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


from configurations.conf import settings
from projects.projects import serializers
from tests.utils import factories as f

#######################################################
# ProjectLogoMixin
#######################################################


def test_project_logo_mixin_serializer_with_logo(monkeypatch):
    project = f.build_project(logo=f.build_image_file())

    monkeypatch.setenv("NINJA_SKIP_REGISTRY", "true")
    data = serializers.ProjectLogoBaseSerializer.model_validate(project)

    assert str(data.logo).startswith(str(settings.BACKEND_URL))

    data = serializers.ProjectLogoBaseSerializer(
        **{"logo": project.logo, "id": project.id}
    )

    assert str(data.logo).startswith(str(settings.BACKEND_URL))


def test_project_logo_mixin_serializer_without_logo():
    data = serializers.ProjectLogoBaseSerializer(logo=None)

    assert data.logo is None
