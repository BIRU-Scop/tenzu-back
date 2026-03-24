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

from contextlib import contextmanager
from io import BytesIO
from tempfile import SpooledTemporaryFile
from typing import IO, Generator

from django.core.files import File
from django.core.files.uploadedfile import InMemoryUploadedFile, SimpleUploadedFile
from PIL import Image

###########################################################
# Binary
###########################################################


@contextmanager
def build_binary_fileio(
    content: bytes = b"some initial text data",
) -> Generator[IO[bytes], None, None]:
    file = SpooledTemporaryFile()
    file.write(content)
    file.seek(0)
    yield file
    file.close()


def build_binary_file(
    name: str = "test",
    format: str = "exe",
    content: bytes = b"some initial text data",
) -> File:
    return File(name=f"{name}.{format}", file=BytesIO(content))


def build_binary_uploadfile(
    name: str = "test",
    format: str = "bin",
    content_type: str = "application/octet-stream",
    content: bytes = b"some initial text data",
) -> InMemoryUploadedFile:
    return SimpleUploadedFile(f"{name}.{format}", content, content_type)


###########################################################
# String
###########################################################


@contextmanager
def build_string_fileio(content: str = "some initial text data") -> IO[bytes]:
    file = SpooledTemporaryFile()
    file.write(content.encode())
    file.seek(0)
    file.close()
    return file


def build_string_file(
    name: str = "test",
    format: str = "txt",
    content: str = "some initial text data",
) -> File:
    return File(name=f"{name}.{format}", file=BytesIO(content.encode()))


def build_string_uploadfile(
    name: str = "test",
    format: str = "txt",
    content_type: str = "text/plain",
    content: str = "some initial text data",
) -> InMemoryUploadedFile:
    file = build_string_file(name, format, content)
    return InMemoryUploadedFile(
        file, None, f"{name}.{format}", content_type, file.size, None, None
    )


###########################################################
# Images
###########################################################


@contextmanager
def build_image_fileio(format: str = "png") -> Generator[IO[bytes], None, None]:
    file = SpooledTemporaryFile()
    pil_image = Image.new("RGBA", size=(50, 50), color=(155, 0, 0))
    pil_image.save(file, format=format)
    file.seek(0)
    yield file
    file.close()


def build_image_file(
    name: str = "test",
    format: str = "png",
) -> File:
    stream = BytesIO()
    pil_image = Image.new("RGBA", size=(50, 50), color=(155, 0, 0))
    pil_image.save(stream, format=format)
    stream.seek(0)
    return File(name=f"{name}.{format}", file=stream)


def build_image_uploadfile(
    name: str = "test",
    format: str = "png",
    content_type: str = "image/png",
) -> InMemoryUploadedFile:
    image = build_image_file(name, format)
    return InMemoryUploadedFile(
        image, None, f"{name}.{format}", content_type, image.size, None, None
    )
