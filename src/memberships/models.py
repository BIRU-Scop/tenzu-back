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

from typing import Any

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models.base import ModelBase
from django_stubs_ext.db.models.manager import ManyRelatedManager

from base.db.mixins import CreatedAtMetaInfoMixin
from base.db.models import BaseModel, LowerSlugField
from base.utils.datetime import timestamp_mics
from base.utils.slug import (
    generate_incremental_int_suffix,
    slugify_uniquely_for_queryset,
)


class RoleBase(ModelBase):
    """
    Meta class to create role tables.
    """

    def __new__(
        cls,
        name,
        bases,
        attrs,
        **kwargs,
    ):
        parents = [b for b in bases if isinstance(b, RoleBase)]
        if not parents:
            return super().__new__(cls, name, bases, attrs, **kwargs)

        try:
            reference_model: type[BaseModel] = kwargs["reference_model"]
            permissions_choices: list = kwargs["permissions_choices"]
        except KeyError as e:
            raise ValueError(
                f"{e.args[0]} must be specified when inheriting from this class"
            ) from e
        membership_classname: str = kwargs.get(
            "membership_classname",
            f"{reference_model._meta.app_label}_memberships.{reference_model._meta.object_name}Membership",
        )

        attrs["permissions"] = ArrayField(
            models.CharField(
                max_length=40, null=False, blank=False, choices=permissions_choices
            ),
            null=False,
            blank=False,
            default=list,
            verbose_name="permissions",
        )
        attrs["users"] = models.ManyToManyField(
            "users.User",
            related_name=f"{reference_model._meta.model_name}_roles",
            through=membership_classname,
            through_fields=("role", "user"),
            verbose_name="users",
        )
        attrs[reference_model._meta.model_name] = models.ForeignKey(
            reference_model,
            null=False,
            blank=False,
            related_name="roles",
            on_delete=models.CASCADE,
            verbose_name=reference_model._meta.verbose_name,
        )
        # Note: Meta is fully overridden, this will need to be changed if we need customisation of Meta in subclasses
        attrs["Meta"] = type(
            "Meta",
            (object,),
            dict(
                verbose_name=f"{reference_model._meta.verbose_name} role",
                verbose_name_plural=f"{reference_model._meta.verbose_name} roles",
                constraints=[
                    models.UniqueConstraint(
                        fields=[reference_model._meta.model_name, "slug"],
                        name=f"%(app_label)s_%(class)s_unique_{reference_model._meta.model_name}_slug",
                    ),
                    models.UniqueConstraint(
                        fields=[reference_model._meta.model_name, "name"],
                        name=f"%(app_label)s_%(class)s_unique_{reference_model._meta.model_name}_name",
                    ),
                ],
                indexes=[
                    models.Index(fields=[reference_model._meta.model_name, "slug"]),
                ],
                ordering=[reference_model._meta.model_name, "order", "name"],
            ),
        )

        def __repr__(self) -> str:
            return f"<{self.__class__.__name__} {self._meta.fields[reference_model._meta.model_name]} {self.slug}>"

        def save(self, *args: Any, **kwargs: Any) -> None:
            if not self.slug:
                self.slug = slugify_uniquely_for_queryset(
                    value=self.name,
                    queryset=self._meta.fields[
                        reference_model._meta.model_name
                    ].roles.all(),
                    generate_suffix=generate_incremental_int_suffix(),
                    use_always_suffix=False,
                )

            Role.save(self, *args, **kwargs)

        attrs["__repr__"] = __repr__
        attrs["save"] = save
        return super().__new__(cls, name, bases, attrs)


class Role(BaseModel, metaclass=RoleBase):
    """
    Abstract class for roles
    You need to pass `reference_model` and `permissions_choices` to meta class argument like so
    class ProjectRole(Role, reference_model=Project, permissions_choices=ProjectPermissions.choices)
    `reference_model` must be the model class for which roles will be added

    - `membership_classname` can be used to customize the class name for the membership through table,
      defaults to projects_memberships.ProjectMembership if `reference_model` is Project
    """

    permissions: list[str]
    name = models.CharField(
        max_length=200, null=False, blank=False, verbose_name="name"
    )
    slug = LowerSlugField(max_length=250, null=False, blank=True, verbose_name="slug")
    order = models.BigIntegerField(
        default=timestamp_mics, null=False, blank=False, verbose_name="order"
    )
    is_owner = models.BooleanField(
        null=False, blank=False, default=False, verbose_name="is_owner"
    )
    editable = models.BooleanField(null=False, default=True, verbose_name="editable")
    users: ManyRelatedManager

    def __str__(self) -> str:
        return self.name

    class Meta:
        abstract = True


class MembershipBase(ModelBase):
    """
    Meta class to create membership through tables.
    """

    def __new__(
        cls,
        name,
        bases,
        attrs,
        **kwargs,
    ):
        parents = [b for b in bases if isinstance(b, MembershipBase)]
        if not parents:
            return super().__new__(cls, name, bases, attrs, **kwargs)

        try:
            reference_model: type[BaseModel] = kwargs["reference_model"]
        except KeyError as e:
            raise ValueError(
                f"{e.args[0]} must be specified when inheriting from this class"
            ) from e

        role_classname: str = kwargs.get(
            "role_classname",
            f"{reference_model._meta.app_label}_memberships.{reference_model._meta.object_name}Role",
        )
        attrs["user"] = models.ForeignKey(
            "users.User",
            null=False,
            blank=False,
            related_name=f"{reference_model._meta.model_name}_memberships",
            on_delete=models.CASCADE,
            verbose_name="user",
        )
        attrs["role"] = models.ForeignKey(
            role_classname,
            null=False,
            blank=False,
            related_name="memberships",
            on_delete=models.RESTRICT,
            verbose_name="role",
        )
        attrs[reference_model._meta.model_name] = models.ForeignKey(
            reference_model,
            null=False,
            blank=False,
            related_name="memberships",
            on_delete=models.CASCADE,
            verbose_name=reference_model._meta.verbose_name,
        )
        # Note: Meta is fully overridden, this will need to be changed if we need customisation of Meta in subclasses
        attrs["Meta"] = type(
            "Meta",
            (object,),
            dict(
                verbose_name=f"{reference_model._meta.verbose_name} membership",
                verbose_name_plural=f"{reference_model._meta.verbose_name} memberships",
                constraints=[
                    models.UniqueConstraint(
                        fields=[reference_model._meta.model_name, "user"],
                        name=f"%(app_label)s_%(class)s_unique_{reference_model._meta.model_name}_user",
                    ),
                ],
                indexes=[
                    models.Index(fields=[reference_model._meta.model_name, "user"]),
                ],
                ordering=[reference_model._meta.model_name, "user"],
            ),
        )

        def __str__(self) -> str:
            return (
                f"{self._meta.fields[reference_model._meta.model_name]} - {self.user}"
            )

        def __repr__(self) -> str:
            return f"<{self.__class__.__name__} {self._meta.fields[reference_model._meta.model_name]} {self.user}>"

        attrs["__str__"] = __str__
        attrs["__repr__"] = __repr__
        return super().__new__(cls, name, bases, attrs)


class Membership(BaseModel, CreatedAtMetaInfoMixin, metaclass=MembershipBase):
    """
    Abstract class for membership, used as `through` table for roles
    You need to pass `reference_model` to meta class argument like so
    class ProjectMembership(Membership, reference_model=Project)
    `reference_model` must be the model class for which memberships are added

    - `role_classname` can be used to customize the class name for the foreignkey to Role
      defaults to projects_memberships.ProjectRole if `reference_model` is Project
    """

    user: models.ForeignKey
    role: models.ForeignKey

    class Meta:
        abstract = True
