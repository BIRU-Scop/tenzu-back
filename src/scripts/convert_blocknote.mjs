import { ServerBlockNoteEditor } from "@blocknote/server-util";
import { createCodeBlockSpec } from "@blocknote/core";
import { codeBlockOptions } from "@blocknote/code-block";
import * as Y from "yjs";
import readline from 'readline';

function getArgs () {
    // support CLI arg --fromFormat="md" or  --fromFormat="html"
    return process.argv.slice(2).reduce((args, arg) => {
        // long arg
        if (arg.slice(0, 2) === "--") {
            const longArg = arg.split("=");
            const longArgFlag = longArg[0].slice(2);
            const longArgValue = longArg.length > 1 ? longArg[1] : true;
            args[longArgFlag] = longArgValue;
        }
        // flags
        else if (arg[0] === "-") {
            const flags = arg.slice(1).split("");
            flags.forEach((flag) => {
                args[flag] = true;
            });
        }
        return args;
    }, {});
}


async function getBlocks(editor, content, fromFormat) {
    let blocks
    if (fromFormat === "html") {
        blocks = await editor.tryParseHTMLToBlocks(content);
    } else if (fromFormat === "md") {
        blocks = await editor.tryParseMarkdownToBlocks(content);
    } else {
        blocks = JSON.parse(content);
    }
    return blocks;
}

async function main() {
    const args = getArgs();
    if (args["fromFormat"] && !["html", "md"].includes(args["fromFormat"])) {
        throw Error("invalid fromFormat argument, supported options are 'html' or 'md'");
    }

    const codeBlock = createCodeBlockSpec(codeBlockOptions);
    const editor = ServerBlockNoteEditor.create({
        codeBlock
    });
    const rl = readline.createInterface({
        input: process.stdin,
        terminal: false
    });

    for await (const line of rl) {
        if (!line.trim()) return;
        try {
            const {id, content} = JSON.parse(line);
            if (!content) {
                process.stdout.write(`${id}:EMPTY\n`);
                return;
            }
            const blocks = await getBlocks(editor, content, args["fromFormat"]);

            const doc = editor.blocksToYDoc(blocks, "document-store");
            const update = Y.encodeStateAsUpdate(doc);
            const hexYjs = Buffer.from(update).toString('hex');

            if (args["fromFormat"]) {
                const hexBlocks = Buffer.from(new TextEncoder("utf-8").encode(JSON.stringify(blocks))).toString('hex');
                process.stdout.write(`${id}:${hexYjs}:${hexBlocks}\n`);
            } else {
                process.stdout.write(`${id}:${hexYjs}\n`);
            }
        } catch (e) {
            // Instead of crashing, we return an error to stdout to not break the pipe
            const errorId = line.includes('"id"') ? JSON.parse(line).id : "unknown";
            process.stderr.write(`Error on object ${errorId}: ${e.message}\n`);
            process.stdout.write(`${errorId}:ERROR\n`);
        }
    }
}

main().then();
