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
"""
URL configuration for configurations project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.urls import path
from django.urls.resolvers import URLPattern, URLResolver

from .api import api

urlpatterns: list[URLPattern | URLResolver] = []

urlpatterns += [
    path("api/v2/", api.urls),
]


if settings.DEBUG:
    from django.contrib import admin
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    from django.urls import re_path

    ##############################################
    # Admin panel
    ##############################################

    urlpatterns += [
        path("admin/", admin.site.urls),
    ]

    ##############################################
    # Media files
    ##############################################

    def mediafiles_urlpatterns(prefix: str) -> list[URLPattern]:
        """
        Method for serve media files with runserver.
        """
        import re

        from django.views.static import serve

        return [
            re_path(
                r"^%s(?P<path>.*)$" % re.escape(prefix.lstrip("/")),
                serve,
                {"document_root": settings.MEDIA_ROOT},
            )
        ]

    urlpatterns += mediafiles_urlpatterns(prefix="/media/")

    ##############################################
    # Static files
    ##############################################

    urlpatterns += staticfiles_urlpatterns(prefix="/static/")
