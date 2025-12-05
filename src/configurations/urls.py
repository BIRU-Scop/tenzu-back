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
from django.urls import include, path
from django.urls.resolvers import URLPattern, URLResolver

from .api import api

urlpatterns: list[URLPattern | URLResolver] = []

urlpatterns += [
    path(f"api/{settings.API_VERSION}/", api.urls),
    path("_allauth/accounts/", include("allauth.urls")),
]


if settings.DEBUG:
    from django.conf.urls.static import static
    from django.contrib import admin

    ##############################################
    # Admin panel
    ##############################################

    urlpatterns += [
        path("admin/", admin.site.urls),
    ]

    ##############################################
    # Media files
    ##############################################

    # you'll need to change the caddy config not to serve the media files directly if you want this route to be used
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

##############################################
# Static files
##############################################
# uncomment only if you need to serve static file with DEBUG=False,
# otherwise the runserver is already doing it for you
# SECURITY WARNING: never uncomment in production
# from django.contrib.staticfiles.urls import staticfiles_urlpatterns
# urlpatterns += staticfiles_urlpatterns(prefix="/static/")
