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

import orjson

from stories.stories.services.blocknote import BlockNoteConverter


def test_convert_blocks_data():
    data = '[{"id":"1166453f-52f7-4dea-af18-245e5d05e9a6","type":"paragraph","props":{"textColor":"default","backgroundColor":"default","textAlignment":"left"},"content":[{"type":"text","text":"azerazerazer","styles":{}}],"children":[]},{"id":"32fb12dd-e776-4831-8dd6-16c96026b313","type":"heading","props":{"textColor":"default","backgroundColor":"default","textAlignment":"left","level":1,"isToggleable":false},"content":[{"type":"text","text":"qsdfqdsf","styles":{}}],"children":[]},{"id":"a8d6fe16-3f18-4f71-982c-69ba5732cdc2","type":"paragraph","props":{"textColor":"default","backgroundColor":"default","textAlignment":"left"},"content":[{"type":"text","text":"c\'est ma story","styles":{}}],"children":[]},{"id":"4c0b279e-9de7-4667-8dbc-edee05e342e1","type":"table","props":{"textColor":"default"},"content":{"type":"tableContent","columnWidths":[null,null],"rows":[{"cells":[{"type":"tableCell","content":[{"type":"text","text":"zazer","styles":{}}],"props":{"colspan":1,"rowspan":1,"backgroundColor":"default","textColor":"default","textAlignment":"left"}},{"type":"tableCell","content":[{"type":"text","text":"azer","styles":{}}],"props":{"colspan":1,"rowspan":1,"backgroundColor":"default","textColor":"default","textAlignment":"left"}}]},{"cells":[{"type":"tableCell","content":[{"type":"text","text":"zaer","styles":{}}],"props":{"colspan":1,"rowspan":1,"backgroundColor":"default","textColor":"default","textAlignment":"left"}},{"type":"tableCell","content":[],"props":{"colspan":1,"rowspan":1,"backgroundColor":"default","textColor":"default","textAlignment":"left"}}]},{"cells":[{"type":"tableCell","content":[{"type":"text","text":"azer","styles":{}}],"props":{"colspan":1,"rowspan":1,"backgroundColor":"default","textColor":"default","textAlignment":"left"}},{"type":"tableCell","content":[],"props":{"colspan":1,"rowspan":1,"backgroundColor":"default","textColor":"default","textAlignment":"left"}}]}]},"children":[]},{"id":"2ccaa64b-33fe-4a75-b992-5198531e5dc4","type":"paragraph","props":{"textColor":"default","backgroundColor":"default","textAlignment":"left"},"content":[{"type":"text","text":"azerazer","styles":{}}],"children":[]},{"id":"7a4b3bb2-8d4a-46d5-afc4-43f25b17c7e9","type":"paragraph","props":{"textColor":"default","backgroundColor":"default","textAlignment":"left"},"content":[],"children":[]},{"id":"fc1482af-5f64-4438-a612-986bbcfd7b43","type":"paragraph","props":{"textColor":"orange","backgroundColor":"default","textAlignment":"left"},"content":[{"type":"text","text":"aze","styles":{}}],"children":[]},{"id":"3cbd9ebc-bd6b-4248-bdef-a096cffad5d2","type":"paragraph","props":{"textColor":"green","backgroundColor":"default","textAlignment":"left"},"content":[{"type":"text","text":"r","styles":{}}],"children":[]},{"id":"2f00a347-ac78-4a47-93dc-78d527ff629e","type":"paragraph","props":{"textColor":"default","backgroundColor":"default","textAlignment":"left"},"content":[{"type":"text","text":"az","styles":{}}],"children":[]},{"id":"5dfc1eb7-d4a0-4dbd-a9fe-8bfb6b7b2777","type":"paragraph","props":{"textColor":"default","backgroundColor":"default","textAlignment":"left"},"content":[{"type":"text","text":"er","styles":{}}],"children":[]},{"id":"e8e15a81-1a7b-444b-b85c-a3fe65df91e4","type":"paragraph","props":{"textColor":"default","backgroundColor":"default","textAlignment":"left"},"content":[],"children":[]},{"id":"7ad4cb1a-11f9-484f-a8f4-840047031782","type":"paragraph","props":{"textColor":"default","backgroundColor":"default","textAlignment":"left"},"content":[{"type":"text","text":"azer","styles":{}}],"children":[]},{"id":"58835732-f4d6-400c-a9be-c73d14822959","type":"paragraph","props":{"textColor":"default","backgroundColor":"default","textAlignment":"left"},"content":[],"children":[]},{"id":"639c8f05-f455-4ebb-9cb2-d2a80b9bf779","type":"paragraph","props":{"textColor":"default","backgroundColor":"default","textAlignment":"left"},"content":[{"type":"text","text":"aze","styles":{}}],"children":[]},{"id":"1b083741-979c-446c-b665-4f717f48807e","type":"paragraph","props":{"textColor":"default","backgroundColor":"default","textAlignment":"left"},"content":[{"type":"text","text":"r","styles":{}}],"children":[]},{"id":"fad89674-19ef-4208-8d57-59c4fafc9562","type":"paragraph","props":{"textColor":"default","backgroundColor":"default","textAlignment":"left"},"content":[{"type":"text","text":"zear","styles":{}}],"children":[]},{"id":"67650f81-0eca-44ad-b0a7-98ab8df54073","type":"paragraph","props":{"textColor":"default","backgroundColor":"default","textAlignment":"left"},"content":[],"children":[]},{"id":"cbc53186-d7ca-48b0-9fba-bcd532c79807","type":"paragraph","props":{"textColor":"default","backgroundColor":"default","textAlignment":"left"},"content":[{"type":"text","text":"zaer","styles":{}}],"children":[]},{"id":"d93922cb-6de9-4e86-8326-59752b056cf1","type":"paragraph","props":{"textColor":"default","backgroundColor":"default","textAlignment":"left"},"content":[],"children":[]},{"id":"727a4c8d-9443-4304-9f13-5e20afaafd9c","type":"paragraph","props":{"textColor":"default","backgroundColor":"default","textAlignment":"left"},"content":[],"children":[]}]'
    converter = BlockNoteConverter()
    with converter:
        string_id, binary_data, block_data = converter.convert(
            {"id": "0", "content": data}
        )
    assert converter._process.poll() is not None
    assert string_id == "0"
    assert isinstance(binary_data, bytes)
    assert block_data is None


def test_convert_html_data():
    data = "<div><p><i>text</i></p><br/><p>In <b>markdown</b></p><br/><h1>Title</h1><br/><ul><li>and</li><li>a</li><li>list</li></ul></div>"
    converter = BlockNoteConverter(source_format="html")
    with converter:
        string_id, binary_data, block_data = converter.convert(
            {"id": "0", "content": data}
        )
    assert converter._process.poll() is not None
    assert string_id == "0"
    assert isinstance(binary_data, bytes)
    assert block_data is not None and orjson.loads(block_data)


def test_convert_markdown_data():
    data = "*text* \nIn **markdown**\n#Title\n- and\n- a\n- list\n"
    converter = BlockNoteConverter(source_format="md")
    with converter:
        string_id, binary_data, block_data = converter.convert(
            {"id": "0", "content": data}
        )
    assert converter._process.poll() is not None
    assert string_id == "0"
    assert isinstance(binary_data, bytes)
    assert block_data is not None and orjson.loads(block_data)
