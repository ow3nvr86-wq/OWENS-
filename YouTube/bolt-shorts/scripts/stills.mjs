// Render QC stills at given times (seconds) from one bundle.
// usage: node scripts/stills.mjs outDir t1 t2 ...
import { bundle } from "@remotion/bundler";
import { selectComposition, renderStill } from "@remotion/renderer";
import path from "node:path";
import fs from "node:fs";

const [outDir, ...times] = process.argv.slice(2);
fs.mkdirSync(outDir, { recursive: true });
const browserExecutable = "/opt/pw-browsers/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell";
const serveUrl = await bundle({ entryPoint: path.resolve("src/index.ts") });
const inputProps = { showCaptions: true, withAudio: false };
const composition = await selectComposition({ serveUrl, id: "MainVideo", inputProps, browserExecutable });
for (const ts of times) {
  const frame = Math.min(959, Math.round(parseFloat(ts) * 30));
  const output = path.join(outDir, `f${String(frame).padStart(3, "0")}.png`);
  await renderStill({ serveUrl, composition, frame, output, inputProps, browserExecutable, imageFormat: "png" });
  process.stdout.write(`${frame} `);
}
console.log("done");
