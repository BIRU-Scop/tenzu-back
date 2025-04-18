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

from django.db import models

from base.utils.datetime import aware_utcnow

#######################################################
# Generic model metadata
#######################################################


class CreatedAtMetaInfoMixin(models.Model):
    created_at = models.DateTimeField(
        null=False,
        blank=False,
        default=aware_utcnow,
        verbose_name="created at",
    )

    class Meta:
        abstract = True


class CreatedByMetaInfoMixin(models.Model):
    created_by = models.ForeignKey(
        "users.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name="created by",
        related_name="%(app_label)s_%(class)s_created_by",
    )

    class Meta:
        abstract = True


class CreatedMetaInfoMixin(CreatedByMetaInfoMixin, CreatedAtMetaInfoMixin):
    class Meta:
        abstract = True


class ModifiedAtMetaInfoMixin(models.Model):
    modified_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="modified at",
    )

    class Meta:
        abstract = True


class DeletedByMetaInfoMixin(models.Model):
    deleted_by = models.ForeignKey(
        "users.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name="deleted by",
        related_name="%(app_label)s_%(class)s_deleted_by",
    )

    class Meta:
        abstract = True


class DeletedAtMetaInfoMixin(models.Model):
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="deleted at",
    )

    class Meta:
        abstract = True


class DeletedMetaInfoMixin(DeletedByMetaInfoMixin, DeletedAtMetaInfoMixin):
    class Meta:
        abstract = True


#######################################################
# Title
#######################################################


class TitleUpdatedMetaInfoMixin(models.Model):
    title_updated_by = models.ForeignKey(
        "users.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name="title updated by",
        related_name="%(app_label)s_%(class)s_title_updated_by",
    )
    title_updated_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="title updated at",
    )

    class Meta:
        abstract = True


#######################################################
# Description
#######################################################


class DescriptionUpdatedMetaInfoMixin(models.Model):
    description_updated_by = models.ForeignKey(
        "users.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name="description updated by",
        related_name="%(app_label)s_%(class)s_description_updated_by",
    )
    description_updated_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="description updated at",
    )

    class Meta:
        abstract = True
