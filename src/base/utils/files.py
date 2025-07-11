# -*- coding: utf-8 -*-
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

import hashlib
import io
from os import path, urandom
from typing import IO, Any, Generator

from django.core.files.base import File as DjangoFile
from django.db.models.fields.files import FieldFile  # noqa
from ninja import UploadedFile

from base.utils.datetime import aware_utcnow
from base.utils.iterators import split_by_n
from base.utils.slug import slugify

File = DjangoFile


def uploadfile_to_file(file: UploadedFile) -> File:
    """
    Convert an `ninja.UploadedFile object to a `File` object. Useful to the ORM.
    """
    return File(name=file.name, file=file.file)


def iterfile(file: File, mode: str | None = "rb") -> Generator[bytes, None, None]:
    """
    Function to iterate over the content of a Django File object.
    This function is useful to iterate over the content of a file so you can stream it.

    :param file: a Django File object
    :type file: File
    :param mode: the mode to open the file
    :type mode: str | None
    :return a generator
    :rtype Generator[bytes, None, None]
    """
    with file.open(mode) as f:
        yield from f


def get_size(file: IO[Any]) -> int:
    """
    Calculate the current size of a file in bytes.

    :param file: any object that satisfy the typing.IO interface
    :type file: typing.IO
    :return the size in bytes
    :rtype int
    """
    current = file.tell()
    size = file.seek(0, io.SEEK_END)
    file.seek(current)
    return size


def normalize_filename(filename: str) -> str:
    """
    Normalize a filename. It will be

      - in lowercase
      - slugified
      - with no more than 100 characters

    :param filename: a filename
    :type filename: str
    :return a normalized filename
    :rtype str
    """
    base, ext = path.splitext(path.basename(filename).lower())
    base = slugify(base)[0:100]
    return f"{base}{ext}"


def get_obfuscated_file_path(instance: Any, filename: str, base_path: str = "") -> str:
    """
    Generates a path for a file by obfuscating it, using a hash as the name of the directory
    in which it will be stored.

    NOTE: This function is useful for use in a Django model with FileField or ImageField to
    define the upload_to attribute.

    :param instance: a Django Model instance
    :type instance: Any
    :param filename: a filename
    :type filename: str
    :param base_path: an optional base path
    :type base_path: str
    :return an obfuscated path
    :rtype str
    """
    basename = normalize_filename(filename)

    hs = hashlib.sha256()
    hs.update(aware_utcnow().isoformat().encode("utf-8", "strict"))
    hs.update(urandom(1024))

    p1, p2, p3, p4, *p5 = split_by_n(hs.hexdigest(), 1)
    hash_part = path.join(p1, p2, p3, p4, "".join(p5))

    return path.join(base_path, hash_part, basename)
