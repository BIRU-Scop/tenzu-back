# Copyright (C) 2026 BIRU
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

import json
import logging
import subprocess
from contextlib import AbstractContextManager
from typing import Literal, TypedDict

from django.conf import settings

logger = logging.getLogger(__name__)

FileFormat = Literal["html", "md"]


class BlockNoteInputData(TypedDict):
    id: str
    content: str


class BlockNoteScriptError(Exception):
    pass


class BlockNoteEmptyOutputError(Exception):
    pass


class BlockNoteConverter(AbstractContextManager):
    def __init__(self, source_format: FileFormat | None = None):
        self.source_format = source_format

    def __enter__(self):
        script_path = settings.BASE_DIR / "scripts" / "convert_blocknote.mjs"
        args = (
            [f"--fromFormat={self.source_format}"]
            if self.source_format is not None
            else []
        )

        self._process = subprocess.Popen(
            ["node", "--max-old-space-size=4096", script_path, *args],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,  # Line buffered
        )
        return self

    def close_process(self) -> tuple[str, str]:
        if self._process.stdin:
            self._process.stdin.close()
        if self._process.poll() is None:
            self._process.terminate()
            try:
                return self._process.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
                return self._process.communicate()
        return "", ""

    def __exit__(self, *exc):
        outs, errs = self.close_process()
        if outs or errs:
            logger.warning(f"leftover data in pipes STDOUT: {outs}, STDERR: {errs}")

    def convert(self, input_data: BlockNoteInputData) -> tuple[str, bytes, str | None]:
        # Check if the process is still active
        if self._process.poll() is not None:
            _, stderr_data = self.close_process()
            raise RuntimeError(
                f"Node.js process terminated unexpectedly with code {self._process.returncode}. Error: {stderr_data}"
            )

        # Send one object as a JSON line to Node
        try:
            # do not use orjson because we need string and orjson dumps gives us bytes
            self._process.stdin.write(json.dumps(input_data) + "\n")
            self._process.stdin.flush()
        except BrokenPipeError:
            _, stderr_data = self.close_process()
            raise RuntimeError(f"Broken pipe: Node.js crashed. Details: {stderr_data}")

        # Read the result (one line)
        line = self._process.stdout.readline()
        if not line:
            _, stderr_data = self.close_process()
            raise BlockNoteEmptyOutputError(f"Error output: {stderr_data}")
        object_id_str, hex_yjs_data = line.strip().split(":", 1)

        if hex_yjs_data in {"ERROR", "EMPTY"}:
            stderr_data = self._process.stderr.readline()
            logger.error(f"convert_blocknote script error: {stderr_data}")
            raise BlockNoteScriptError(stderr_data)

        json_block_data = None
        if self.source_format is not None:
            hex_yjs_data, block_hex_data = hex_yjs_data.strip().split(":", 1)
            json_block_data = bytes.fromhex(block_hex_data).decode("utf-8")
        binary_yjs_data = bytes.fromhex(hex_yjs_data)
        return object_id_str, binary_yjs_data, json_block_data
