// THE WORLD — news-image-20261125 rebuild #4.
// Copy-only entrypoint: puts the rendered broadsheet where the harness expects it.
import { copyFileSync, chmodSync, existsSync, mkdirSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const src = join(here, "entry.png");
const outDir = process.env.MAKEFUN_OUTPUT_DIR ?? "/output";
const dest = join(outDir, "entry.png");

if (!existsSync(src)) {
  console.error("entry.png missing next to main.ts");
  process.exit(1);
}
mkdirSync(outDir, { recursive: true });
copyFileSync(src, dest);
chmodSync(dest, 0o644);
console.log("wrote " + dest);
// v4 final: copy-only entrypoint, chmod 0644, verified with draw.py + verify.py 20/20.
