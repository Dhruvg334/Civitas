import { existsSync } from 'fs';
import { spawnSync } from 'child_process';
import { resolve } from 'path';

const isRoot = existsSync(resolve(process.cwd(), 'apps/web'));
const targetDir = isRoot ? resolve(process.cwd(), 'apps/web') : process.cwd();

console.log(`[Civitas Build] Compiling Next.js in ${targetDir}...`);
const cmd = process.platform === 'win32' ? 'npm.cmd' : 'npm';

const res = spawnSync(cmd, ['run', 'build'], {
  cwd: targetDir,
  stdio: 'inherit',
  shell: process.platform === 'win32',
  env: process.env,
});

if (res.status !== 0) {
  process.exit(res.status ?? 1);
}
