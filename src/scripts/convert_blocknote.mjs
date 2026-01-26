import { blocksToYDoc } from "@blocknote/core/yjs";
import { BlockNoteEditor, createCodeBlockSpec } from "@blocknote/core";
import { codeBlockOptions } from "@blocknote/code-block";
import * as Y from "yjs";
import readline from 'readline';


const codeBlock = createCodeBlockSpec(codeBlockOptions);
const editor = BlockNoteEditor.create({
    codeBlock
});

const rl = readline.createInterface({
    input: process.stdin,
    terminal: false
});

rl.on('line', (line) => {
    if (!line.trim()) return;
    try {
        const { id, description } = JSON.parse(line);
        if (!description) {
            process.stdout.write(`${id}:EMPTY\n`);
            return;
        }

        const blocks = JSON.parse(description);
        const doc = blocksToYDoc(editor, blocks, "document-store");
        const update = Y.encodeStateAsUpdate(doc);
        const hex = Buffer.from(update).toString('hex');

        process.stdout.write(`${id}:${hex}\n`);
    } catch (e) {
        // Instead of crashing, we return an error to stdout to not break the pipe
        const errorId = line.includes('"id"') ? JSON.parse(line).id : "unknown";
        process.stderr.write(`Error on story ${errorId}: ${e.message}\n`);
        process.stdout.write(`${errorId}:ERROR\n`);
    }
});
