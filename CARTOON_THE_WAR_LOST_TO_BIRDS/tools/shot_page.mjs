// screenshot a test page's canvas: node tools/shot_page.mjs page.html out.png
import { createRequire } from 'module'; const { chromium } = createRequire(import.meta.url)('playwright'); import fs from 'fs'; import path from 'path'; import { serve } from './serve.mjs';
const [page, out] = process.argv.slice(2);
const root = path.join(path.dirname(new URL(import.meta.url).pathname), '..', 'web');
const { server, port } = await serve(root);
const b = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const p = await b.newPage();
p.on('console', m => console.log('[page]', m.text())); p.on('pageerror', e => console.log('[error]', e.message));
await p.goto(`http://127.0.0.1:${port}/${page}`); await p.waitForFunction('window.done === true', null, { timeout: 120000 });
const data = await p.evaluate(() => document.getElementById('c').toDataURL('image/png'));
fs.writeFileSync(out, Buffer.from(data.split(',')[1], 'base64'));
await b.close(); server.close(); console.log('wrote', out);
