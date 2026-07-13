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

import factory
from django.core.exceptions import FieldDoesNotExist
from factory.declarations import PostGenerationContext

from tests.utils.utils import add_to_selected_instance_cache


class Factory(factory.django.DjangoModelFactory):
    class Meta:
        strategy = factory.CREATE_STRATEGY
        model = None
        abstract = True
        skip_postgeneration_save = True

    @classmethod
    def _after_postgeneration(cls, instance, create, results=None):
        super()._after_postgeneration(instance, create, results)
        cache_values = {}
        # set related cache to prevent DB query when the related object has not been built
        for field_name, value in results.items():
            if value is not None:
                # If value is set, the related cache will be filled naturally by django's internal mechanisms
                continue
            try:
                field = instance._meta.get_field(field_name)
            except FieldDoesNotExist:
                continue
            if field.is_relation and (field.one_to_one or field.one_to_many):
                cache_values[field_name] = value
        add_to_selected_instance_cache(instance, cache_values)


class OptionalRelatedFactory(factory.RelatedFactory):
    """
    A related factory that will default to None for the related object
    if none of the related object properties have been set.
    If any related property is set, the class behave as normal by creating the related object.
    Useful for related field where you want to default to an empty relation.
    inspired by https://blog.bmispelon.rocks/articles/2024/2024-05-03-optional-subfactories-for-factory_boy.html
    """

    pass

    def call(self, instance, step, context):
        if not context.value_provided and not context.extra:
            context = PostGenerationContext(
                value_provided=True, value=None, extra=context.extra
            )
        return super().call(instance, step, context)
