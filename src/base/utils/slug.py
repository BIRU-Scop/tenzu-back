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

import random
from typing import Generator, Type

from slugify import slugify

from base.db.models import Model, QuerySet


def generate_incremental_int_suffix() -> Generator[str, None, None]:
    """
    Generates a suffix an incremental integer

    :return an integer suffix
    :rtype str
    """
    n = 0
    while True:
        n += 1
        yield f"{n}"


def generate_int_suffix() -> Generator[str, None, None]:
    """
    Generates a suffix consisting of 3 random numbers.

    :return a text suffix
    :rtype str
    """
    yield f"{random.randint(0,999):03}"


def slugify_uniquely(
    value: str,
    model: Type[Model],
    slugfield: str = "slug",
    generate_suffix: Generator[str, None, None] | None = None,
    use_always_suffix: bool = True,
    template: str = "{base}-{suffix}",
) -> str:
    """
    Returns a slug on a name which is unique within a model's table

    :param value: base text for the slug
    :type value: str
    :param model: a django model
    :type queryset: Type[Model]
    :param slugfield: name of the field that contains the slug (default `slug`)
    :type slugfield: str
    :param generate_suffix: function that generates a suffix (default one returns random chars)
    :type generate_suffix: Generator[str, None, None]
    :param use_always_suffix: always use a suffix in the slug when it's True
    :type use_always_suffix: bool
    :return a unique slug
    :rtype str
    """

    return slugify_uniquely_for_queryset(
        value=value,
        queryset=model.objects.all(),
        slugfield=slugfield,
        generate_suffix=generate_suffix,
        use_always_suffix=use_always_suffix,
        template=template,
    )


def slugify_uniquely_for_queryset(
    value: str,
    queryset: QuerySet[Model],
    slugfield: str = "slug",
    generate_suffix: Generator[str, None, None] | None = None,
    use_always_suffix: bool = True,
    template: str = "{base}-{suffix}",
) -> str:
    """
    Returns a slug on a name which is unique within a Django queryset. This method adds suffix only if it is necessary.

    :param value: base text for the slug
    :type value: str
    :param queryset: a django queryset
    :type queryset: QuerySet
    :param slugfield: name of the field that contains the slug (default `slug`)
    :type slugfield: str
    :param generate_suffix: function that generates a suffix (default one returns an incremental integer)
    :type generate_suffix: Generator[str, None, None]
    :param use_always_suffix: always use a suffix in the slug when it's True
    :type use_always_suffix: bool
    :return a unique slug
    :rtype str
    """

    generator = generate_suffix or generate_int_suffix()
    suffix = next(generator) if use_always_suffix else ""
    potential = base = (
        slugify(value) or "null"
    )  # "null" serves when slugify(value) returns empty string
    while True:
        if suffix:
            potential = template.format(base=base, suffix=suffix)
        if not queryset.filter(**{slugfield: potential}).exists():
            return potential
        suffix = next(generator)
