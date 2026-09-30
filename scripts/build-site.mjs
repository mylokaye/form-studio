import { mkdir, readFile, writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const projectRoot = fileURLToPath(new URL("..", import.meta.url));
const preview = await readFile(resolve(projectRoot, "examples/preview.html"), "utf8");
const original = await readFile(resolve(projectRoot, "examples/restyle/original.html"), "utf8");
const styled = await readFile(resolve(projectRoot, "examples/restyle/styled.html"), "utf8");
const output = resolve(projectRoot, "dist/server/index.js");

await mkdir(resolve(projectRoot, "dist/server"), { recursive: true });

const worker = `const pages = new Map(${JSON.stringify([
  ["/", preview], ["/index.html", preview], ["/test.html", preview], ["/examples/preview.html", preview],
  ["/restyle/original.html", original], ["/restyle/styled.html", styled],
  ["/examples/restyle/original.html", original], ["/examples/restyle/styled.html", styled],
])});

export default {
  async fetch(request) {
    const url = new URL(request.url);
    if (pages.has(url.pathname)) {
      return new Response(pages.get(url.pathname), {
        headers: { "content-type": "text/html; charset=utf-8" }
      });
    }
    return new Response("Not found", { status: 404 });
  }
};
`;

await writeFile(output, worker, "utf8");
console.log(`Built ${output}`);
